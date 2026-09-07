#!/usr/bin/env python3
"""Build the Tiri Reference Manual as one document per chapter.

The chapter sources are written as fragments of book.adoc: they begin at level 1
(`== Title`) and refer to each other with plain `<<anchor>>` cross-references.
This script wraps each fragment in a standalone document, preserves the chapter
and appendix numbering used by the full manual, and rewrites cross-chapter
references so that they resolve to the sibling output instead of dangling.

Usage:
    ./build_chapters.py                      # build every chapter as PDF
    ./build_chapters.py --backend html       # build every chapter as HTML
    ./build_chapters.py ch10 appendix_a      # build a subset (prefix match)
    ./build_chapters.py -o /tmp/out          # choose the output directory
    ./build_chapters.py --cross-refs text    # unlinked cross-chapter references
    ./build_chapters.py --keep               # retain the generated AsciiDoc
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
BOOK = SRC / 'book.adoc'

INCLUDE_RE = re.compile(r'^include::([^\[]+)\[\]')
ATTRIBUTE_RE = re.compile(r'^:([\w-]+!?):\s*(.*)$')
ANCHOR_RE = re.compile(r'^\[\[([\w:.-]+?)(?:,\s*(.+?))?\]\]\s*$')
SHORT_ANCHOR_RE = re.compile(r'^\[#([\w:.-]+?)(?:[,.][^\]]*)?\]\s*$')
HEADING_RE = re.compile(r'^(=+)\s+(.*\S)\s*$')
XREF_RE = re.compile(r'<<([\w:.-]+?)(?:,\s*([^<>]*?))?>>')

# Attributes that only make sense for the complete book.
SKIP_ATTRIBUTES = {'toc', 'toclevels', 'index', 'pdf-themesdir', 'copyright'}


def read(path):
    return path.read_text(encoding='utf-8').split('\n')


def parse_book():
    """Return (header_attributes, author, [(file, part_title)]) from book.adoc."""
    attributes, author, entries = [], '', []
    part = ''
    in_header = True
    for line in read(BOOK):
        if in_header:
            if line.startswith('= '):
                continue
            if not author and line.strip() and not line.startswith(':'):
                author = line.strip()
                continue
            match = ATTRIBUTE_RE.match(line)
            if match:
                if match.group(1).rstrip('!') not in SKIP_ATTRIBUTES:
                    attributes.append(line)
                continue
            if line.startswith('toc::'):
                in_header = False
            continue
        if line.startswith('= '):
            part = line[2:].strip()
        match = INCLUDE_RE.match(line)
        if match and part:
            entries.append((match.group(1).strip(), part))
    return attributes, author, entries


def index_anchors(entries, numbers):
    """Map every anchor id to its source file and full-book reference text."""
    anchors = {}
    for name, _ in entries:
        lines = read(SRC / name)
        kind, value = numbers[name]
        counts = [0, 0, 0]
        heading_labels = {}

        for i, line in enumerate(lines):
            heading = HEADING_RE.match(line)
            if not heading:
                continue
            level, title = len(heading.group(1)), heading.group(2)
            if level == 2:
                if kind == 'appendix':
                    heading_labels[i] = f'Appendix {chr(ord("A") + value)}, {title}'
                else:
                    heading_labels[i] = f'Chapter {value}, {title}'
                continue
            if 3 <= level <= 5:
                depth = level - 2
                counts[depth - 1] += 1
                for index in range(depth, len(counts)):
                    counts[index] = 0
                prefix = chr(ord('A') + value) if kind == 'appendix' else str(value)
                number = '.'.join([prefix] + [str(count) for count in counts[:depth]])
                heading_labels[i] = f'Section {number}, {title}'

        for i, line in enumerate(lines):
            match = ANCHOR_RE.match(line) or SHORT_ANCHOR_RE.match(line)
            if not match:
                continue
            reftext = match.lastindex == 2 and match.group(2) or None
            if not reftext:
                for follow in range(i + 1, min(i + 4, len(lines))):
                    if follow in heading_labels:
                        reftext = heading_labels[follow]
                        break
                    if lines[follow].strip() and not lines[follow].startswith('['):
                        break
            anchors[match.group(1)] = (name, reftext)
    return anchors


def numbering(entries):
    """Assign a chapter number or appendix letter to each included file."""
    numbers, chapter, appendix = {}, 0, 0
    for name, _ in entries:
        if (SRC / name).read_text(encoding='utf-8').find('\n[appendix]\n') >= 0:
            numbers[name] = ('appendix', appendix)
            appendix += 1
        else:
            chapter += 1
            numbers[name] = ('chapter', chapter)
    return numbers


def label(kind, value, title):
    if kind == 'appendix':
        return f'Appendix {chr(ord("A") + value)} — {title}'
    return f'Chapter {value} — {title}'


def rewrite_xrefs(name, lines, anchors, mode, output_names):
    """Point cross-chapter references at sibling output, or flatten them."""
    def substitute(match):
        target, text = match.group(1), match.group(2)
        entry = anchors.get(target)
        if not entry or entry[0] == name:
            return match.group(0)
        caption = text or entry[1] or target
        if mode == 'text':
            return caption
        return f'link:{output_names[entry[0]]}#{target}[{caption}]'

    in_code = False
    output = []
    for line in lines:
        if re.match(r'^(-{4,}|\.{4,}|`{3,})\s*$', line):
            in_code = not in_code
        output.append(line if in_code else XREF_RE.sub(substitute, line))
    return output


def build(args):
    attributes, author, entries = parse_book()
    files = [name for name, _ in entries]
    numbers = numbering(entries)
    anchors = index_anchors(entries, numbers)
    output_suffix = '.pdf' if args.backend == 'pdf' else '.html'
    output_names = {name: Path(name).stem + output_suffix for name in files}

    out_dir = Path(args.output).resolve()
    work_dir = out_dir / '.adoc'
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(exist_ok=True)
    if args.backend == 'html':
        for name in ('docinfo.html', 'docinfo-footer.html'):
            shutil.copy2(SRC / name, work_dir / name)

    selected = [(n, p) for n, p in entries
                if not args.chapters or any(n.startswith(c) for c in args.chapters)]
    if not selected:
        sys.exit(f'No chapter matches {args.chapters}')

    failures = []
    for name, part in selected:
        lines = read(SRC / name)
        kind, value = numbers[name]
        title = next(HEADING_RE.match(l).group(2) for l in lines if HEADING_RE.match(l))
        stem = Path(name).stem

        (work_dir / name).write_text(
            '\n'.join(rewrite_xrefs(name, lines, anchors, args.cross_refs, output_names)),
            encoding='utf-8')

        if args.backend == 'pdf':
            header = [f'= Tiri Reference Manual: {label(kind, value, title)}', author]
            header += attributes
            header += [
                f':pdf-themesdir: {SRC}',
                f':imagesdir: {SRC / "images"}',
            ]
        else:
            header = [f'= {label(kind, value, title)}']
            header += [attribute for attribute in attributes
                       if not attribute.startswith((':revdate:', ':revremark:', ':title-logo-image:'))]
            header.append(':imagesdir: images')
        header += [':toc: macro', ':toclevels: 3']
        # Asciidoctor seeds its numbering from these counters, so pre-setting them
        # to the preceding value keeps each chapter numbered as it is in the book.
        if kind == 'chapter' and value > 1:
            header.append(f':chapter-number: {value - 1}')
        elif kind == 'appendix' and value > 0:
            header.append(f':appendix-number: {chr(ord("A") + value - 1)}')
        if part:
            header.append(f':part-title: {part}')
        header += ['', 'toc::[]', '', f'include::{name}[]', '']
        wrapper = work_dir / f'_{stem}.adoc'
        wrapper.write_text('\n'.join(header), encoding='utf-8')

        target = out_dir / output_names[name]
        command = [
            'asciidoctor-pdf' if args.backend == 'pdf' else 'asciidoctor',
            '-a', 'source-highlighter=rouge',
            '-r', str(SRC / 'tiri_lexer.rb'),
            '-r', str(SRC / 'tiri_ebnf.rb'),
            '-r', str(SRC / 'tiri_compact_table.rb'),
            '-r', str(SRC / 'tiri_compact_toc.rb'),
            '-r', str(SRC / 'tiri_compact_list.rb'),
            '-o', str(target),
        ]
        if args.backend == 'html':
            command += ['-d', 'book', '-a', 'docinfo=shared']
        command.append(str(wrapper))
        print(f'  {label(kind, value, title)} -> {target.name}', flush=True)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            failures.append((name, result.stderr.strip()))
        elif result.stderr.strip() and args.verbose:
            print(result.stderr.strip(), file=sys.stderr)

    if not args.keep:
        shutil.rmtree(work_dir, ignore_errors=True)

    for name, error in failures:
        print(f'FAILED: {name}\n{error}', file=sys.stderr)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('chapters', nargs='*', help='file name prefixes to build')
    parser.add_argument('--backend', choices=['pdf', 'html'], default='pdf',
                        help='output format (default: pdf)')
    parser.add_argument('-o', '--output', default=str(SRC.parent / 'tiri-manual-chapters'),
                        help='output directory (default: ../tiri-manual-chapters)')
    parser.add_argument('--cross-refs', choices=['link', 'text'], default='link',
                        help='cross-chapter references become sibling links or plain text')
    parser.add_argument('--keep', action='store_true', help='retain the generated AsciiDoc')
    parser.add_argument('-v', '--verbose', action='store_true', help='show Asciidoctor warnings')
    sys.exit(build(parser.parse_args()))


if __name__ == '__main__':
    main()
