def string_with_arrows(text, pos_start, pos_end):
    if not text:
        return ''

    lines = text.splitlines()

    start_line = max(0, min(pos_start.ln, len(lines) - 1))
    end_line = max(0, min(pos_end.ln, len(lines) - 1))

    result = []

    for line_index in range(start_line, end_line + 1):
        line = lines[line_index]

        if line_index == start_line:
            col_start = max(0, min(pos_start.col, len(line)))
        else:
            col_start = 0

        if line_index == end_line:
            col_end = max(0, min(pos_end.col, len(line)))
        else:
            col_end = len(line)

        if col_end <= col_start:
            col_end = min(col_start + 1, len(line))

        result.append(line)

        marker_length = max(1, col_end - col_start)
        result.append(' ' * col_start + '^' * marker_length)

    return '\n'.join(result).replace('\t', '    ')
