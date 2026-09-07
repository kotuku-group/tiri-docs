# -*- coding: utf-8 -*- #
# frozen_string_literal: true

# Compact rendering for reference tables in the PDF backend.
#
# Asciidoctor PDF sizes every table from the 'table' theme category, and roles
# on a table are ignored: convert_table never consults the 'role_*' theme keys
# that paragraphs and other blocks pick up, so '[.small]' has no effect on a
# table.  This extension restores that control for tables carrying the 'compact'
# role, which the reference appendices use for their long constant-and-
# description listings.
#
# A table opts in by carrying the 'compact' role:
#
#   [cols="2,5",role=compact]
#   |===
#   |Constant |Description
#   |===
#
# Any 'table_compact_*' keys in the theme are applied over their 'table_*'
# counterparts for the duration of the table, so the treatment can be tuned from
# tiri-theme.yml without editing this file.  For example:
#
#   table:
#     compact:
#       font-size: 8.5
#       cell-padding: 2
#       head:
#         font-size: 9
#
# Codespans inherit the reduced size automatically because 'codespan font-size'
# is expressed in em, and is therefore relative to the enclosing cell.
#
# Without a 'table: compact: font-size:' key the role falls back to
# DEFAULT_FONT_SCALE of the table font size that is otherwise in effect.
#
# Usage with Asciidoctor:
#   asciidoctor-pdf -r ./tiri_compact_table.rb document.adoc

require 'asciidoctor/pdf'

module Asciidoctor
   module PDF
      module TiriCompactTable
         DEFAULT_FONT_SCALE = 0.85

         def convert_table node
            return super unless node.has_role? 'compact'

            overrides = compact_theme_overrides.dup
            overrides['table_font_size'] ||= (@theme.table_font_size || @theme.base_font_size) * DEFAULT_FONT_SCALE

            saved = {}
            overrides.each_key {|key| saved[key] = @theme[key] }
            overrides.each {|key, value| @theme[key] = value }
            begin
               super
            ensure
               saved.each {|key, value| @theme[key] = value }
            end
         end

         private

         # Map the 'table_compact_*' theme keys onto their 'table_*' counterparts.  The
         # prefix is stripped rather than matched against a fixed list, so nested keys such
         # as 'table_compact_head_font_size' resolve to 'table_head_font_size'.
         def compact_theme_overrides
            @compact_theme_overrides ||= @theme.each_pair.each_with_object({}) do |(key, value), accum|
               accum[%(table_#{(key.to_s.slice 14, key.length)})] = value if (key.to_s.start_with? 'table_compact_')
            end
         end
      end

      Converter.prepend TiriCompactTable
   end
end
