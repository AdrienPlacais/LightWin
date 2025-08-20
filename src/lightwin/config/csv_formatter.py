"""Provide helper function to split configuration entries.

Idea is to have properly formatter configuration tables in the HTML
documentation.

"""

import re


def format_long_columns(long: str, max_width: int) -> str:
    """Format cell content to fit within ``max_width``.

    A cell spanning over several lines should start and end by a single ``"``
    character. Two line skips should be inserted where the line breaks.

    """
    if len(long) < max_width:
        return long
    chunks = chunk(long, max_width)
    joined = "\n\n".join(chunks)
    return joined


OPEN_PUNCT = "([{"
CLOSE_PUNCT = ".,:;!?)]}"


def _lex(text: str) -> list[str]:
    """Tokenize text.

    Tokenize into:

      - roles like :class:`.Accelerator` (keeps trailing punctuation)
      - backtick blocks like `...` possibly with adjacent leading '(' or
        trailing ')','.', etc.
      - words (no spaces)
      - single punctuation tokens (if not attached to backtick/role)

    Spaces are skipped; spacing is decided at assembly time.

    """
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue

        # role starting at i: :name:`...`
        if ch == ":":
            m = re.match(r":[A-Za-z0-9_]+:`[^`]+`", text[i:])
            if m:
                token = m.group(0)
                end = i + m.end()
                # attach contiguous trailing punctuation (.,:;!?) or closing )]}.
                while end < n and text[end] in CLOSE_PUNCT:
                    token += text[end]
                    end += 1
                # attach a preceding opening punctuation if it was the immediate previous token
                if (
                    tokens
                    and i > 0
                    and text[i - 1] in OPEN_PUNCT
                    and tokens[-1] == text[i - 1]
                ):
                    tokens.pop()
                    token = text[i - 1] + token
                tokens.append(token)
                i = end
                continue

        # backtick block
        if ch == "`":
            j = text.find("`", i + 1)
            if j == -1:
                # unmatched - treat as word-ish
                k = i + 1
                while (
                    k < n
                    and not text[k].isspace()
                    and text[k] not in "`()[]{}"
                ):
                    k += 1
                tokens.append(text[i:k])
                i = k
                continue
            token = text[i : j + 1]
            end = j + 1
            # attach contiguous trailing punctuation
            while end < n and text[end] in CLOSE_PUNCT:
                token += text[end]
                end += 1
            # if an opening punctuation directly precedes the backtick and we previously emitted it,
            # attach that opening punct as a prefix to keep the group together.
            if (
                tokens
                and i > 0
                and text[i - 1] in OPEN_PUNCT
                and tokens[-1] == text[i - 1]
            ):
                tokens.pop()
                token = text[i - 1] + token
            tokens.append(token)
            i = end
            continue

        # single punctuation
        if ch in OPEN_PUNCT + CLOSE_PUNCT:
            tokens.append(ch)
            i += 1
            continue

        # normal word (stop at whitespace, backtick or bracket; also stop before a role start)
        j = i
        while j < n and not text[j].isspace() and text[j] not in "`()[]{}":
            # if a role starts here, break
            if text[j] == ":" and re.match(r":[A-Za-z0-9_]+:`", text[j:]):
                break
            j += 1
        tokens.append(text[i:j])
        i = j

    return tokens


def _visible_len(token: str) -> int:
    """Length used for wrapping decisions.

    - For backtick/role tokens, do NOT count the backticks or the `:role:`
      prefix.
    - But DO count any prefix opening punctuation and suffix closing
      punctuation.

    """
    m = re.match(
        r"(?P<prefix>[\(\[\{]*)?(?:(?::(?P<rolename>[A-Za-z0-9_]+):)?`(?P<inner>[^`]+)`)(?P<suffix>[\)\]\}\.,:;!?]*)?$",
        token,
    )
    if m:
        prefix = m.group("prefix") or ""
        inner = m.group("inner") or ""
        suffix = m.group("suffix") or ""
        return len(prefix) + len(inner) + len(suffix)

    # fallback: if something like ":role:rest" (without backticks) appears,
    # ignore the :role: length
    m2 = re.match(
        r"(?P<prefix>[\(\[\{]*)?:(?P<rolename>[A-Za-z0-9_]+):(?P<rest>.*)$",
        token,
    )
    if m2:
        prefix = m2.group("prefix") or ""
        rest = m2.group("rest") or ""
        return len(prefix) + len(rest)

    return len(token)


def _needs_space_between(prev: str, token: str) -> bool:
    """Decide whether to insert a space between prev and token.

    - No space before a closing punctuation (.,:;!?)}]).
    - No space after an opening punctuation ([( { ) (i.e. if prev ends with
      opening).
    - Otherwise, insert a space.

    """
    if not prev:
        return False
    if token and token[0] in CLOSE_PUNCT:
        return False
    if prev and prev[-1] in OPEN_PUNCT:
        return False
    return True


def _split_normal_word(word: str, max_width: int) -> list[str]:
    """Hyphenate word when needed (allowed to sit next to other words)"""
    if len(word) <= max_width:
        return [word]
    out: list[str] = []
    w = word
    while len(w) > max_width:
        out.append(w[: max_width - 1] + "-")
        w = w[max_width - 1 :]
    out.append(w)
    return out


def _split_backtick(token: str, max_width: int) -> list[str]:
    """Split a backtick token into wrapped chunks.

    Where each chunk's inner content length is <= max_width (max_width applies
    to the inner content).

    - Keeps prefix opening punctuation only on the first chunk.
    - Keeps suffix closing punctuation only on the last chunk.
    - Prefers splitting at '_' first; otherwise splits at spaces.
    - If any atomic piece (between delimiters) is longer than max_width,
      returns [token]
      (do not hyphenate inside variable names).

    """
    m = re.match(
        r"(?P<prefix>[\(\[\{]*)?`(?P<inner>[^`]+)`(?P<suffix>[\)\]\}\.,:;!?]*)?$",
        token,
    )
    if not m:
        return [token]
    prefix = m.group("prefix") or ""
    inner = m.group("inner") or ""
    suffix = m.group("suffix") or ""

    # prefer underscores
    if "_" in inner:
        parts = inner.split("_")
        if any(len(p) > max_width for p in parts):
            return [token]
        pieces = [p + "_" for p in parts[:-1]] + [parts[-1]]
        chunks: list[str] = []
        cur = ""
        for piece in pieces:
            if not cur:
                cur = piece
            elif len(cur) + len(piece) <= max_width:
                cur += piece
            else:
                chunks.append(cur)
                cur = piece
        if cur:
            chunks.append(cur)
        out: list[str] = []
        for i, ch in enumerate(chunks):
            s = "`" + ch + "`"
            if i == 0 and prefix:
                s = prefix + s
            if i == len(chunks) - 1 and suffix:
                s = s + suffix
            out.append(s)
        return out
    else:
        # split on spaces (do not keep trailing spaces inside pieces)
        words = inner.split(" ")
        if any(len(w) > max_width for w in words):
            return [token]
        chunks = []
        cur = ""
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= max_width:
                cur = cur + " " + w
            else:
                chunks.append(cur)
                cur = w
        if cur:
            chunks.append(cur)
        out: list[str] = []
        for i, ch in enumerate(chunks):
            s = "`" + ch + "`"
            if i == 0 and prefix:
                s = prefix + s
            if i == len(chunks) - 1 and suffix:
                s = s + suffix
            out.append(s)
        return out


def _targeted_split_backtick(
    token: str, rem: int, max_width: int
) -> list[str] | None:
    """Try to split the backtick token so that:

      - the first chunk (with prefix) fits within 'rem' (available room on
        current line),
      - and the rest (with suffix) can be split to chunks that fit max_width
        lines.

    We attempt to choose the largest first-chunk (by trying split points from
    the end). For stability with the test-suite we require the first chunk to
    contain at least two atomic parts (so we avoid silly 1-word-first-chunk
    splits).

    """
    m = re.match(
        r"(?P<prefix>[\(\[\{]*)?`(?P<inner>[^`]+)`(?P<suffix>[\)\]\}\.,:;!?]*)?$",
        token,
    )
    if not m:
        return None
    prefix = m.group("prefix") or ""
    inner = m.group("inner") or ""
    suffix = m.group("suffix") or ""
    prefix_len = len(prefix)

    if "_" in inner:
        parts = inner.split("_")
        if any(len(p) > max_width for p in parts):
            return None

        def join_parts(a, b):
            seg = "_".join(parts[a:b])
            return seg + ("_" if b < len(parts) else "")

    else:
        parts = inner.split(" ")
        if any(len(p) > max_width for p in parts):
            return None

        def join_parts(a, b):
            return " ".join(parts[a:b])

    n = len(parts)
    # try splits; require first chunk to contain at least two parts for stability
    for k in range(n - 1, 1, -1):
        first_inner = join_parts(0, k)
        if prefix_len + len(first_inner) <= rem:
            rest_inner = join_parts(k, n)
            rest_token = "`" + rest_inner + "`" + suffix
            rest_chunks = _split_backtick(rest_token, max_width)
            if rest_chunks:
                first_chunk = prefix + "`" + first_inner + "`"
                return [first_chunk] + rest_chunks
            # else continue trying smaller k
    return None


def chunk(text: str, max_width: int) -> list[str]:
    """Split text into lines of length <= max_width (best-effort).

    - reST roles (`:role:`...``) are atomic; the `:role:` prefix is not
      counted.
    - Backtick tokens are split at '_' (preferred) or spaces (no hyphenation
      inside words).
    - Normal words wrap on spaces; very long words are hyphenated.
    - Spacing rules: no space before closing punctuation; no space after
      opening punctuation.

    """
    tokens = _lex(text)
    lines: list[str] = []
    cur_text = ""
    cur_len = 0  # visible length

    for tok in tokens:
        is_role = tok.startswith(":") and "`" in tok
        is_backtick = tok.startswith("`") or (
            tok and tok[0] in OPEN_PUNCT and "`" in tok
        )

        if is_role:
            t_chunks = [tok]
        elif is_backtick:
            add_space = (
                1 if cur_len > 0 and _needs_space_between(cur_text, tok) else 0
            )
            full_len = _visible_len(tok)

            if cur_len + add_space + full_len <= max_width:
                t_chunks = [tok]
            else:
                rem = max_width - cur_len - add_space
                t_try = None
                if rem >= 1 and ("_" in tok or " " in tok):
                    t_try = _targeted_split_backtick(tok, rem, max_width)
                t_chunks = t_try if t_try else _split_backtick(tok, max_width)
        else:
            # normal word
            add_space = (
                1 if cur_len > 0 and _needs_space_between(cur_text, tok) else 0
            )
            if cur_len + add_space + len(tok) <= max_width:
                t_chunks = [tok]
            else:
                t_chunks = _split_normal_word(tok, max_width)

        # emit chunks
        for i, chunk_tok in enumerate(t_chunks):
            add_space = (
                1
                if cur_len > 0 and _needs_space_between(cur_text, chunk_tok)
                else 0
            )
            if cur_len + add_space + _visible_len(chunk_tok) > max_width:
                # start a new line
                if cur_text:
                    lines.append(cur_text)
                cur_text = chunk_tok
                cur_len = _visible_len(chunk_tok)
            else:
                if add_space:
                    cur_text += " "
                    cur_len += 1
                cur_text += chunk_tok
                cur_len += _visible_len(chunk_tok)

    if cur_text:
        lines.append(cur_text)
    return lines
