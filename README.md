# MWParse

A parser for a custom, customizable markup language, inspired by
Markdown and aimed at writers of prose. Compiles to HTML.

## Rationale

I previously have used Markdown for typing general prose, and while it
was fairly simple to learn and unobtrusive, it was lacking ways to
express important markups, such as indented sections, centred text,
underlines and strikethroughs. While more complicated systems such as
LaTeX or even raw HTML exist, I find them too cluttered to properly
concentrate on the content of what's being typed.

Thus, the three design requirements of MWParse were *expressivity*,
that a potentially-large number of markups be supported, *simplicity*,
that the language should be fairly simple to understand and modify,
and *cleanliness*, that the language should not get in the way of the
text.

To that end, MWParse's syntax structure is based on Markdown. However,
MWParse is neither a strict subset nor superset of Markdown. MWParse's
by default supports far more syntax elements that Markdown, for
example `%` which creates a block of centred text. In contrast,
several features of Markdown remain unimplemented by MWParse due to
the latter's focus on prose (e.g. lists and hyperlinking).

Incidentally, this document is both valid Markdown and and MWParse.

## The Language

The language itself is specified in two config files, passed to
MWparse via the `-b` and `-l` command line options. One specifies the
block elements, while the other specifies inline elements. Each config
file consists of a number of tab-separated entries, one per line.

### Block Elements

A line in the block config file consists of either 3 or 4
tab-separated entries. The first is the token that appears in a
document to create a block of that type. The second and third are the
HTML tags to emit to begin and end the block, respectively. The
fourth, if present (otherwise defaulting to "yes") specifies whether
more blocks can be nested within a block of this type (e.g. in the
default block.cfg, indents can nest but headings can't).

By default, the innermost block then contains a <p> element into which
the text is placed. This does not occur when a block is specified to
not nest.

Only the first line of a block needs, and in fact is allowed to have,
the block token. The current block will end once the parser sees a
blank line. To end some of a nested block, the "blank" line should
instead contain only the tokens of the blocks to be continued.

### Inline Elements

A line in the inline config file can consist of 2, 3 or 4
tab-separated entries. A two-entry column is a simple replacement rule
--- whenever the token in the first column is encountered, it is
replaced with the token in the second. A three-entry column specifies
a paired token, where the first instance is replaced with the entry in
the second column and the second with that in the third. The fourth
column being "no" specifies no nesting, or all following tokens are
ignored until the current token is matched (allowing something like
the raw code segments of Markdown, for instance).
