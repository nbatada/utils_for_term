#!/usr/bin/env python3
# Table Manipulator on command line (tm)

import sys
import argparse
import re
import pandas as pd
import codecs # For handling escape sequences
from io import StringIO # For handling piped input with pandas

def parse_column_arg(value, df_columns, is_header_present, arg_name="column"):
    """
    Parses a column argument, converting 1-indexed to 0-indexed, or resolving column name.
    Returns the 0-indexed integer position.
    """
    try:
        # If it's a number, assume 1-indexed and convert to 0-indexed
        col_idx = int(value)
        if col_idx < 1:
            raise ValueError(f"Error: {arg_name} index '{value}' must be 1 or greater (1-indexed).")
        if col_idx - 1 >= len(df_columns): # Check if 0-indexed is out of bounds
             # Allow to-col to be one past the last column for insertion
            if arg_name == "--to-col" and col_idx - 1 == len(df_columns):
                return col_idx - 1
            else:
                raise IndexError(f"Error: {arg_name} index '{value}' (1-indexed) is out of bounds. Max column index is {len(df_columns)}.")
        return col_idx - 1
    except ValueError as e:
        # If not a number, assume it's a column name (only if header is present)
        if not is_header_present:
            raise ValueError(f"Error: Cannot use column name '{value}' for {arg_name} when no header is present (--header=None). Use 1-indexed integer.")
        if value not in df_columns:
            raise ValueError(f"Error: Column '{value}' not found in header for {arg_name}. Available columns: {list(df_columns)}.")
        return df_columns.get_loc(value) # Get 0-indexed position by name
    except IndexError as e:
        raise e # Re-raise if it's an IndexError from bounds check

def parse_multiple_columns_arg(values, df_columns, is_header_present, arg_name="columns"):
    """
    Parses a comma-separated string of column indices/names, returning a list of 0-indexed integers.
    """
    if values.lower() == "all":
        return list(range(len(df_columns)))
    
    col_indices = []
    for val in values.split(','):
        val = val.strip()
        if not val:
            continue
        try:
            col_indices.append(parse_column_arg(val, df_columns, is_header_present, arg_name))
        except (ValueError, IndexError) as e:
            raise type(e)(f"Error parsing {arg_name} '{values}': {e}") # Re-raise with context
    return col_indices


def clean_string_for_header_and_data(s):
    """Applies cleanup rules to a string."""
    if not isinstance(s, str):
        return s # Return as is if not a string (e.g., NaN, None)
    s = s.lower()
    s = s.replace(' ', '_')
    s = re.sub(r'[^\w_]', '', s) # Remove non-alphanumeric or underscore characters
    s = re.sub(r'_{2,}', '_', s) # Squeeze multiple underscores
    return s

def print_verbose(args, message):
    """Prints a message to stderr if verbose mode is enabled."""
    if args.verbose:
        sys.stderr.write(f"VERBOSE: {message}\n")

def main():
    parser = argparse.ArgumentParser(
        description="A command-line tool for manipulating table fields.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # Global arguments
    parser.add_argument(
        "-s", "--sep", default="\t",
        help="Input/output field separator (default: tab). "
             "Supports escape sequences like '\\t', '\\n'."
    )
    parser.add_argument(
        "--header", type=str, default="0", choices=["0", "None"],
        help="Specify header row. '0' for first row as header (default), "
             "'None' for no header. Column operations are 1-indexed relative to data."
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose output for debugging to stderr."
    )

    subparsers = parser.add_subparsers(dest="operation", help="Available operations")

    # --- Move Operation ---
    parser_move = subparsers.add_parser(
        "move", help="Move a column from one position to another."
    )
    parser_move.add_argument(
        "-i", "--from-col", required=True,
        help="Source column index (1-indexed) or name."
    )
    parser_move.add_argument(
        "-j", "--to-col", required=True,
        help="Destination column index (1-indexed) or name. If beyond existing columns, appends."
    )

    # --- Insert Operation ---
    parser_insert = subparsers.add_parser(
        "insert", help="Insert a new column with a specified value."
    )
    parser_insert.add_argument(
        "-i", "--col-idx", required=True,
        help="Column index (1-indexed) or name where the new column will be inserted."
    )
    parser_insert.add_argument(
        "-v", "--value", required=True,
        help="Value to insert into the new column. Supports escape sequences."
    )
    parser_insert.add_argument(
        "--new-header", default="new_column",
        help="Header name for the new column (default: 'new_column')."
    )

    # --- Delete Operation ---
    parser_delete = subparsers.add_parser(
        "delete", help="Delete one or more columns."
    )
    parser_delete.add_argument(
        "-i", "--cols-to-delete", required=True,
        help="Comma-separated list of column indices (1-indexed) or names to delete. Use 'all' to delete all columns."
    )

    # --- Query Operation ---
    parser_query = subparsers.add_parser(
        "query", help="Filter rows based on pattern matching in a specific column."
    )
    parser_query_group = parser_query.add_mutually_exclusive_group(required=True)
    parser_query.add_argument(
        "-i", "--col-idx", required=True,
        help="Column index (1-indexed) or name to query."
    )
    parser_query_group.add_argument(
        "-p", "--pattern",
        help="Regular expression pattern to search for."
    )
    parser_query_group.add_argument(
        "--starts-with",
        help="String to check if column value starts with."
    )
    parser_query_group.add_argument(
        "--ends-with",
        help="String to check if column value ends with."
    )

    # --- Split Operation ---
    parser_split = subparsers.add_parser(
        "split", help="Split a column by a delimiter into multiple new columns."
    )
    parser_split.add_argument(
        "-i", "--col-idx", required=True,
        help="Column index (1-indexed) or name to split."
    )
    parser_split.add_argument(
        "-d", "--delimiter", required=True,
        help="Delimiter to split the column by. Supports escape sequences."
    )
    parser_split.add_argument(
        "--new-header-prefix", default="split_col",
        help="Prefix for new headers (e.g., 'split_col_1', 'split_col_2')."
    )

    # --- Merge Operation ---
    parser_merge = subparsers.add_parser(
        "merge", help="Merge two or more columns with a specified separator into a new column."
    )
    parser_merge.add_argument(
        "-i", "--cols-to-merge", required=True,
        help="Comma-separated list of column indices (1-indexed) or names to merge."
    )
    parser_merge.add_argument(
        "-d", "--delimiter", default="",
        help="Delimiter to use when merging columns (default: no delimiter). Supports escape sequences."
    )
    parser_merge.add_argument(
        "--new-header", default="merged_column",
        help="Header name for the new merged column (default: 'merged_column')."
    )
    parser_merge.add_argument(
        "-j", "--target-col-idx",
        help="1-indexed target column index or name for the new merged column. "
             "If not specified, replaces the first column in --cols-to-merge."
    )

    # --- Translate Operation ---
    parser_translate = subparsers.add_parser(
        "translate", help="Map values in a column using a two-column dictionary file or direct translation."
    )
    parser_translate.add_argument(
        "-i", "--col-idx", required=True,
        help="Column index (1-indexed) or name to translate."
    )
    
    # Mutually exclusive group for translation source
    translate_source_group = parser_translate.add_mutually_exclusive_group(required=True)
    translate_source_group.add_argument(
        "-d", "--dict-file",
        help="Path to a two-column file (key<sep>value) for translation mapping, "
             "using the main --sep as the dictionary file separator."
    )
    translate_source_group.add_argument( # This will be the trigger for single replacement mode
        "--from-val",
        help="Original value to translate from (for single translation). Supports escape sequences."
    )
    parser_translate.add_argument( # This argument is not part of the M-E group, but depends on --from-val
        "--to-val",
        help="New value to translate to (for single translation). Supports escape sequences."
    )
    parser_translate.add_argument(
        "--regex", action="store_true",
        help="Treat --from-val as a regular expression pattern when performing single translation (default is literal)."
    )

    parser_translate.add_argument(
        "--new-header", default="_translated",
        help="Suffix for the new translated column's header (e.g., 'OriginalCol_translated'). "
             "If only '_translated' is given, it's appended to the original header. "
             "If a full name is given, it replaces it. (default: '_translated')"
    )
    parser_translate.add_argument(
        "--in-place", action="store_true",
        help="Modify the column in place instead of adding a new column."
    )

    # --- Sort Operation ---
    parser_sort = subparsers.add_parser(
        "sort", help="Sort the table by one or more columns."
    )
    parser_sort.add_argument(
        "-i", "--by", required=True,
        help="Comma-separated list of column indices (1-indexed) or names to sort by."
    )
    parser_sort.add_argument(
        "--desc", action="store_true",
        help="Sort in descending order (default is ascending)."
    )

    # --- Cleanup Header Operation ---
    parser_cleanup_header = subparsers.add_parser(
        "cleanup_header", help="Clean up header names: remove special chars, replace spaces with underscores, lowercase."
    )

    # --- Cleanup Data Operation ---
    parser_cleanup_data = subparsers.add_parser(
        "cleanup_data", help="Clean up values in specified columns: remove special chars, replace spaces with underscores, lowercase."
    )
    parser_cleanup_data.add_argument(
        "-i", "--cols-to-clean", required=True,
        help="Comma-separated list of column indices (1-indexed) or names to clean. Use 'all' to clean all columns."
    )

    # --- Prefix Add Operation ---
    parser_prefix_add = subparsers.add_parser(
        "prefix_add", help="Add a string prefix to values in specified columns."
    )
    parser_prefix_add.add_argument(
        "-i", "--cols-to-prefix", required=True,
        help="Comma-separated list of column indices (1-indexed) or names to add prefix to. Use 'all' for all columns."
    )
    parser_prefix_add.add_argument(
        "-v", "--string", required=True,
        help="String to add as a prefix. Supports escape sequences."
    )
    parser_prefix_add.add_argument(
        "-d", "--delimiter", default="",
        help="Delimiter between the prefix and the original value (default: no delimiter). Supports escape sequences."
    )

    # --- Summarize Operation ---
    parser_summarize = subparsers.add_parser(
        "summarize", help="List top N most frequent values for specified columns."
    )
    parser_summarize.add_argument(
        "-i", "--cols-to-summarize", required=True,
        help="Comma-separated list of column indices (1-indexed) or names to summarize. Use 'all' for all columns."
    )
    parser_summarize.add_argument(
        "-n", "--top-n", type=int, default=5,
        help="Number of top frequent values to list (default: 5)."
    )

    # --- Strip Operation ---
    parser_strip = subparsers.add_parser(
        "strip", help="Remove specified characters/pattern from column values, adding a new column."
    )
    parser_strip.add_argument(
        "-i", "--col-idx", required=True,
        help="Column index (1-indexed) or name to strip characters from."
    )
    parser_strip.add_argument(
        "-p", "--pattern", required=True,
        help="Regular expression pattern to remove from values."
    )
    parser_strip.add_argument(
        "--new-header", default="_stripped",
        help="Suffix for the new stripped column's header (e.g., 'OriginalCol_stripped'). "
             "If only '_stripped' is given, it's appended to the original header. "
             "If a full name is given, it replaces it. (default: '_stripped')"
    )
    parser_strip.add_argument(
        "--in-place", action="store_true",
        help="Modify the column in place instead of adding a new column."
    )

    # --- View Operation ---
    parser_view = subparsers.add_parser(
        "view", help="Print input data in a nicely formatted table with row numbers."
    )
    parser_view.add_argument(
        "--max-rows", type=int, default=20,
        help="Maximum number of rows to display (default: 20)."
    )
    parser_view.add_argument(
        "--max-cols", type=int, default=None,
        help="Maximum number of columns to display. Default: all columns."
    )

    # --- Cut Operation ---
    parser_cut = subparsers.add_parser(
        "cut", help="Selectively display columns that match a given string or regex pattern in their headers/indices."
    )
    parser_cut.add_argument(
        "-p", "--pattern", required=True,
        help="String or regular expression pattern to match against column headers/indices."
    )
    parser_cut.add_argument(
        "--regex", action="store_true",
        help="Treat the pattern as a regular expression (default is literal string match)."
    )


    # --- View Header Operation ---
    parser_viewheader = subparsers.add_parser(
        "viewheader", help="List each column name (or default Pandas index if no header) and its 1-indexed position."
    )


    args = parser.parse_args()

    # If no operation is specified (e.g., just `field_manipulate`), print help
    if not hasattr(args, 'operation') or args.operation is None:
        parser.print_help()
        sys.exit(0)

    # Decode separator for reading/writing CSV
    input_sep = codecs.decode(args.sep, 'unicode_escape')
    # Use !r to get the safe representation of the string for verbose output
    print_verbose(args, f"Using separator: {input_sep!r}")

    # Read input from stdin into a pandas DataFrame
    header_param = 0 if args.header == "0" else None
    is_header_present = (args.header == "0")
    
    try:
        csv_data = StringIO(sys.stdin.read())
        # Check if input is empty before reading to avoid EmptyDataError if operation doesn't need data
        if csv_data.seek(0, 2) == 0 and args.operation not in ["viewheader", "view"]: # only check for empty if operation needs data
             sys.stderr.write("Error: Input data is empty.\n")
             sys.exit(1)
        csv_data.seek(0) # Reset stream position to beginning
        
        df = pd.read_csv(csv_data, sep=input_sep, header=header_param, dtype=str)
        print_verbose(args, f"Initial DataFrame shape: {df.shape}")
        if is_header_present:
            print_verbose(args, f"Initial Headers: {list(df.columns)}")

    except pd.errors.EmptyDataError:
        # Handle cases where input might be empty for operations that require data
        if args.operation not in ["viewheader", "view", "summarize"]: # Summarize might be called on empty for empty output
            sys.stderr.write("Error: Input data is empty for this operation. Please provide data.\n")
            sys.exit(1)
        else: # For view/viewheader on empty input, proceed with empty DF
            df = pd.DataFrame()
            print_verbose(args, "Input data is empty. Proceeding with an empty DataFrame for view/viewheader.")
            if is_header_present: # If header was '0' but data empty, pandas might create no columns, handle this
                df = pd.DataFrame(columns=[]) # Ensure columns is an empty list, not default int index

    except Exception as e:
        sys.stderr.write(f"Error reading input data: {e}\n")
        sys.exit(1)


    # If no header, ensure pandas uses integer column names (0, 1, 2, ...)
    if not is_header_present:
        df.columns = list(range(df.shape[1]))
        print_verbose(args, "No header detected. Using 0-indexed integer column names.")


    # --- Perform the chosen operation ---
    if args.operation == "move":
        try:
            from_col_0_idx = parse_column_arg(args.from_col, df.columns, is_header_present, "--from-col")
            to_col_0_idx_user = parse_column_arg(args.to_col, df.columns, is_header_present, "--to-col")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        # Adjust to_col_0_idx if it's beyond the current max column index for correct insertion
        to_col_0_idx = min(to_col_0_idx_user, df.shape[1])
        
        print_verbose(args, f"Moving column '{df.columns[from_col_0_idx]}' (0-indexed: {from_col_0_idx}) to position (0-indexed: {to_col_0_idx}).")
        
        col_to_move_name = df.columns[from_col_0_idx]
        col_to_move_data = df.pop(col_to_move_name) # pop removes column and returns it

        df.insert(to_col_0_idx, col_to_move_name, col_to_move_data)
            
    elif args.operation == "insert":
        try:
            col_0_idx = parse_column_arg(args.col_idx, df.columns, is_header_present, "--col-idx")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        insert_value = codecs.decode(args.value, 'unicode_escape')
        new_col_name = args.new_header
        
        print_verbose(args, f"Inserting column at position (0-indexed: {col_0_idx}) with value '{insert_value}' and new header '{new_col_name}'.")

        # Ensure new column name is unique if header is present
        if is_header_present and new_col_name in df.columns:
            original_new_col_name = new_col_name
            i = 1
            while f"{original_new_col_name}_{i}" in df.columns:
                i += 1
            new_col_name = f"{original_new_col_name}_{i}"
            print_verbose(args, f"Header '{original_new_col_name}' already exists. Using unique header '{new_col_name}'.")

        df.insert(col_0_idx, new_col_name, insert_value)
            
    elif args.operation == "delete":
        try:
            cols_to_delete_0_idx = parse_multiple_columns_arg(args.cols_to_delete, df.columns, is_header_present, "--cols-to-delete")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        cols_to_delete_names = [df.columns[i] for i in cols_to_delete_0_idx]
        print_verbose(args, f"Deleting columns: {cols_to_delete_names} (0-indexed: {cols_to_delete_0_idx}).")
        
        df = df.drop(columns=cols_to_delete_names)
        
    elif args.operation == "query":
        try:
            col_0_idx = parse_column_arg(args.col_idx, df.columns, is_header_present, "--col-idx")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        target_col_name = df.columns[col_0_idx]
        target_col = df.iloc[:, col_0_idx].astype(str)
        
        if args.pattern:
            try:
                print_verbose(args, f"Querying column '{target_col_name}' with regex pattern: '{args.pattern}'.")
                df = df[target_col.str.contains(args.pattern, regex=True, na=False)]
            except re.error as e:
                sys.stderr.write(f"Error: Invalid regular expression pattern '{args.pattern}': {e}\n")
                sys.exit(1)
        elif args.starts_with:
            print_verbose(args, f"Querying column '{target_col_name}' for values starting with: '{args.starts_with}'.")
            df = df[target_col.str.startswith(args.starts_with, na=False)]
        elif args.ends_with:
            print_verbose(args, f"Querying column '{target_col_name}' for values ending with: '{args.ends_with}'.")
            df = df[target_col.str.endswith(args.ends_with, na=False)]

    elif args.operation == "split":
        try:
            col_0_idx = parse_column_arg(args.col_idx, df.columns, is_header_present, "--col-idx")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        delimiter = codecs.decode(args.delimiter, 'unicode_escape')
        original_col_name = df.columns[col_0_idx]
        
        print_verbose(args, f"Splitting column '{original_col_name}' by delimiter {delimiter!r}.")

        split_cols_df = df.iloc[:, col_0_idx].astype(str).str.split(delimiter, expand=True).fillna('')
        
        # Generate new header names for split columns
        new_split_headers = []
        for i in range(split_cols_df.shape[1]):
            base_header = f"{args.new_header_prefix}_{i + 1}"
            if is_header_present:
                # Suggest a header based on original column name for clarity
                potential_header = f"{original_col_name}_{base_header}"
                if potential_header not in df.columns:
                    new_split_header = potential_header
                else: # Fallback to generic if already taken
                    j = 1
                    while f"{original_col_name}_{base_header}_{j}" in df.columns:
                        j += 1
                    new_split_header = f"{original_col_name}_{base_header}_{j}"
            else: # No header, use generic
                new_split_header = base_header
            new_split_headers.append(new_split_header)
        split_cols_df.columns = new_split_headers
        print_verbose(args, f"New split column headers: {new_split_headers}.")

        # Drop the original column and concatenate new ones
        df = df.drop(columns=[original_col_name])
        df = pd.concat([df.iloc[:, :col_0_idx], split_cols_df, df.iloc[:, col_0_idx:]], axis=1)

    elif args.operation == "merge":
        try:
            cols_to_merge_0_idx = parse_multiple_columns_arg(args.cols_to_merge, df.columns, is_header_present, "--cols-to-merge")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        if not cols_to_merge_0_idx:
            sys.stderr.write("Error: No columns specified for merge operation.\n")
            sys.exit(1)

        delimiter = codecs.decode(args.delimiter, 'unicode_escape')
        cols_to_merge_names = [df.columns[i] for i in cols_to_merge_0_idx]
        print_verbose(args, f"Merging columns: {cols_to_merge_names} with delimiter {delimiter!r}.")
        
        # Create the merged column
        merged_col_data = df.iloc[:, cols_to_merge_0_idx[0]].astype(str)
        for i in range(1, len(cols_to_merge_0_idx)):
            merged_col_data = merged_col_data + delimiter + df.iloc[:, cols_to_merge_0_idx[i]].astype(str)
        
        # Determine the insertion point and new column name
        if args.target_col_idx is not None:
            try:
                insert_loc_0_idx = parse_column_arg(str(args.target_col_idx), df.columns, is_header_present, "--target-col-idx")
            except (ValueError, IndexError) as e:
                sys.stderr.write(f"{e}\n")
                sys.exit(1)
        else:
            insert_loc_0_idx = cols_to_merge_0_idx[0] # Default to replacing the first merged column

        new_col_name = args.new_header
        if is_header_present and new_col_name in df.columns:
            original_new_col_name = new_col_name
            i = 1
            while f"{original_new_col_name}_{i}" in df.columns:
                i += 1
            new_col_name = f"{original_new_col_name}_{i}"
            print_verbose(args, f"Header '{original_new_col_name}' already exists. Using unique header '{new_col_name}'.")

        # Drop original columns (descending order to avoid shifting issues)
        cols_to_drop_names = [df.columns[idx] for idx in sorted(cols_to_merge_0_idx, reverse=True)]
        df = df.drop(columns=cols_to_drop_names)
        
        # Insert the new merged column
        df.insert(min(insert_loc_0_idx, df.shape[1]), new_col_name, merged_col_data.reset_index(drop=True))
        print_verbose(args, f"Merged column '{new_col_name}' inserted at position (0-indexed: {min(insert_loc_0_idx, df.shape[1])}).")

    elif args.operation == "translate":
        try:
            col_0_idx = parse_column_arg(args.col_idx, df.columns, is_header_present, "--col-idx")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        original_col_name = df.columns[col_0_idx]
        translated_col_data = None

        if args.dict_file:
            translation_map = {}
            try:
                print_verbose(args, f"Loading translation map from '{args.dict_file}' using separator {input_sep!r}.")
                with open(args.dict_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(input_sep, 1) # Use the main separator for dict file
                        if len(parts) == 2:
                            translation_map[parts[0]] = parts[1]
                        else:
                            sys.stderr.write(f"Warning: Skipping malformed line in dictionary file: '{line}'\n")
                print_verbose(args, f"Loaded {len(translation_map)} entries for translation.")
            except FileNotFoundError:
                sys.stderr.write(f"Error: Dictionary file not found: '{args.dict_file}'\n")
                sys.exit(1)
            except Exception as e:
                sys.stderr.write(f"Error reading dictionary file: {e}\n")
                sys.exit(1)
            translated_col_data = df.iloc[:, col_0_idx].astype(str).apply(lambda x: translation_map.get(x, x))
        elif args.from_val:
            if not args.to_val:
                sys.stderr.write("Error: --to-val must be specified when using --from-val.\n")
                sys.exit(1)

            from_val_decoded = codecs.decode(args.from_val, 'unicode_escape')
            to_val_decoded = codecs.decode(args.to_val, 'unicode_escape')

            print_verbose(args, f"Translating values in column '{original_col_name}' from '{from_val_decoded}' to '{to_val_decoded}' {'(regex)' if args.regex else '(literal)'}.")
            try:
                translated_col_data = df.iloc[:, col_0_idx].astype(str).str.replace(
                    from_val_decoded, to_val_decoded, regex=args.regex, n=-1
                )
            except re.error as e:
                sys.stderr.write(f"Error: Invalid regular expression pattern '{from_val_decoded}': {e}\n")
                sys.exit(1)
        else:
            sys.stderr.write("Error: For translate operation, either --dict-file or --from-val (with --to-val) must be specified.\n")
            sys.exit(1)

        # Determine new header name
        if args.in_place:
            print_verbose(args, f"Translating column '{original_col_name}' in place.")
            df.iloc[:, col_0_idx] = translated_col_data
        else:
            if args.new_header.startswith("_"): # Suffix mode
                new_col_name = original_col_name + args.new_header
            else: # Full name mode
                new_col_name = args.new_header
            
            if is_header_present and new_col_name in df.columns:
                original_new_col_name = new_col_name
                i = 1
                while f"{original_new_col_name}_{i}" in df.columns:
                    i += 1
                new_col_name = f"{original_new_col_name}_{i}"
                print_verbose(args, f"Header '{original_new_col_name}' already exists. Using unique header '{new_col_name}'.")

            # Insert the new translated column immediately after the original
            df.insert(col_0_idx + 1, new_col_name, translated_col_data.reset_index(drop=True))
            print_verbose(args, f"Translated column '{new_col_name}' inserted after '{original_col_name}'.")

    elif args.operation == "sort":
        try:
            sort_cols_0_idx = parse_multiple_columns_arg(args.by, df.columns, is_header_present, "--by")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        sort_by_columns = [df.columns[idx] for idx in sort_cols_0_idx]
        print_verbose(args, f"Sorting by columns: {sort_by_columns} in {'descending' if args.desc else 'ascending'} order.")
        
        # Sort the DataFrame. Pandas sort handles non-numeric columns correctly by default.
        df = df.sort_values(by=sort_by_columns, ascending=not args.desc, kind='stable')

    elif args.operation == "cleanup_header":
        if not is_header_present:
            sys.stderr.write("Warning: No header specified (--header=None). 'cleanup_header' has no effect.\n")
            print_verbose(args, "Skipping cleanup_header as no header is present.")
        else:
            original_headers = list(df.columns)
            df.columns = [clean_string_for_header_and_data(col) for col in df.columns]
            print_verbose(args, f"Header cleaned. Original: {original_headers}, New: {list(df.columns)}")

    elif args.operation == "cleanup_data":
        try:
            cols_to_clean_0_idx = parse_multiple_columns_arg(args.cols_to_clean, df.columns, is_header_present, "--cols-to-clean")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)

        cols_to_clean_names = [df.columns[i] for i in cols_to_clean_0_idx]
        print_verbose(args, f"Cleaning data in columns: {cols_to_clean_names}.")
        
        for col_0_idx in cols_to_clean_0_idx:
            df.iloc[:, col_0_idx] = df.iloc[:, col_0_idx].apply(clean_string_for_header_and_data)

    elif args.operation == "prefix_add":
        try:
            cols_to_prefix_0_idx = parse_multiple_columns_arg(args.cols_to_prefix, df.columns, is_header_present, "--cols-to-prefix")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        prefix_string = codecs.decode(args.string, 'unicode_escape')
        prefix_delimiter = codecs.decode(args.delimiter, 'unicode_escape')
        
        cols_to_prefix_names = [df.columns[i] for i in cols_to_prefix_0_idx]
        print_verbose(args, f"Adding prefix '{prefix_string}' with delimiter {prefix_delimiter!r} to columns: {cols_to_prefix_names}.")

        for col_0_idx in cols_to_prefix_0_idx:
            df.iloc[:, col_0_idx] = df.iloc[:, col_0_idx].astype(str).apply(lambda x: f"{prefix_string}{prefix_delimiter}{x}")

    elif args.operation == "summarize":
        try:
            cols_to_summarize_0_idx = parse_multiple_columns_arg(args.cols_to_summarize, df.columns, is_header_present, "--cols-to-summarize")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        if not cols_to_summarize_0_idx:
            sys.stderr.write("Error: No columns specified for summarize operation.\n")
            sys.exit(1)

        summary_output = []
        for col_0_idx in cols_to_summarize_0_idx:
            col_name_for_summary = df.columns[col_0_idx] if is_header_present else f"Column_{col_0_idx + 1}"
            
            top_values = df.iloc[:, col_0_idx].value_counts().head(args.top_n)
            
            summary_output.append(f"--- Summary for {col_name_for_summary} (Top {args.top_n}) ---")
            if top_values.empty:
                summary_output.append("No data to summarize in this column.")
            else:
                for value, count in top_values.items():
                    summary_output.append(f"'{value}': {count}")
            summary_output.append("\n")
        
        sys.stderr.write("\n".join(summary_output))
        sys.exit(0) # Exit after summarizing

    elif args.operation == "strip":
        try:
            col_0_idx = parse_column_arg(args.col_idx, df.columns, is_header_present, "--col-idx")
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        
        original_col_name = df.columns[col_0_idx]
        
        try:
            stripped_col_data = df.iloc[:, col_0_idx].astype(str).str.replace(args.pattern, '', regex=True)
        except re.error as e:
            sys.stderr.write(f"Error: Invalid regular expression pattern '{args.pattern}': {e}\n")
            sys.exit(1)

        if args.in_place:
            print_verbose(args, f"Stripping pattern '{args.pattern}' from column '{original_col_name}' in place.")
            df.iloc[:, col_0_idx] = stripped_col_data
        else:
            print_verbose(args, f"Stripping pattern '{args.pattern}' from column '{original_col_name}', adding a new column.")
            # Determine new header name
            if args.new_header.startswith("_"): # Suffix mode
                new_col_name = original_col_name + args.new_header
            else: # Full name mode
                new_col_name = args.new_header
            
            if is_header_present and new_col_name in df.columns:
                original_new_col_name = new_col_name
                i = 1
                while f"{original_new_col_name}_{i}" in df.columns:
                    i += 1
                new_col_name = f"{original_new_col_name}_{i}"
                print_verbose(args, f"Header '{original_new_col_name}' already exists. Using unique header '{new_col_name}'.")

            # Insert the new stripped column immediately after the original
            df.insert(col_0_idx + 1, new_col_name, stripped_col_data.reset_index(drop=True))
            print_verbose(args, f"Stripped column '{new_col_name}' inserted after '{original_col_name}'.")

    elif args.operation == "view":
        print_verbose(args, f"Viewing data. Max rows: {args.max_rows}, Max cols: {args.max_cols}.")
        # Temporarily set display options for pandas
        pd.set_option('display.max_rows', args.max_rows)
        pd.set_option('display.max_columns', args.max_cols)
        pd.set_option('display.width', None) # Auto-detect width
        pd.set_option('display.colheader_justify','left')

        # Use to_string for consistent output, including index (row numbers)
        sys.stdout.write(df.to_string(index=True, header=is_header_present) + '\n')
        
        # Reset display options to default (optional, but good practice)
        pd.reset_option('display.max_rows')
        pd.reset_option('display.max_columns')
        pd.reset_option('display.width')
        pd.reset_option('display.colheader_justify')

        sys.exit(0) # Exit after viewing

    elif args.operation == "cut":
        pattern = args.pattern
        print_verbose(args, f"Cutting columns with pattern '{pattern}' (regex: {args.regex}).")
        
        selected_columns = []
        for col_name in df.columns:
            if args.regex:
                try:
                    if re.search(pattern, str(col_name)):
                        selected_columns.append(col_name)
                except re.error as e:
                    sys.stderr.write(f"Error: Invalid regular expression pattern '{pattern}': {e}\n")
                    sys.exit(1)
            else: # Literal string match
                if pattern in str(col_name):
                    selected_columns.append(col_name)
        
        if not selected_columns:
            sys.stderr.write(f"Warning: No columns matched the pattern '{pattern}'. Outputting empty data.\n")
            df = pd.DataFrame(columns=[]) # Create empty DataFrame if no match
        else:
            df = df[selected_columns]
            print_verbose(args, f"Selected columns: {selected_columns}.")

    elif args.operation == "viewheader":
        print_verbose(args, "Listing headers and their 1-indexed positions.")
        header_output = []
        if df.empty and not df.columns.empty: # Case where header exists but no data rows
             # If columns attribute has names but dataframe is empty, view those column names
            for i, col_name in enumerate(df.columns):
                header_output.append(f"{i+1}\t{col_name}")
        elif not df.empty or (df.empty and not is_header_present): # Regular case or empty, no header
            current_columns_list = list(df.columns) # Get current column names (can be integers if no header)
            for i, col_name in enumerate(current_columns_list):
                if is_header_present:
                    header_output.append(f"{i+1}\t{col_name}")
                else:
                    header_output.append(f"{i+1}\tColumn_{i+1}") # Generic name if no header
        
        if not header_output and is_header_present:
             # This means header=0 was specified, but input was empty, so pandas couldn't infer columns.
             # In this edge case, it's truly empty, no columns to list.
             sys.stderr.write("No columns found to display. The input might be empty or malformed.\n")
        else:
            sys.stdout.write("\n".join(header_output) + '\n')
        
        sys.exit(0) # Exit after viewheader


    # Output the modified DataFrame to standard output.
    # Write header if it was present
    try:
        if is_header_present:
            df.to_csv(sys.stdout, sep=input_sep, index=False, header=True, encoding='utf-8')
        else:
            df.to_csv(sys.stdout, sep=input_sep, index=False, header=False, encoding='utf-8')
    except BrokenPipeError:
        # Catch BrokenPipeError if downstream command closes pipe early
        sys.stderr.write("BrokenPipeError: Output pipe closed by downstream command. Exiting gracefully.\n")
        sys.exit(0) # Exit cleanly, as the output was likely received by the user

if __name__ == "__main__":
    main()

