# -*- coding: utf-8 -*- #
# frozen_string_literal: true

# Compact rendering for description lists and the index in the PDF backend.
#
# Asciidoctor PDF sizes description list terms from the 'description_list_term'
# theme category and the definitions themselves from the ambient prose font, so
# neither responds to a role on the list: convert_dlist never consults the
# 'role_*' theme keys that paragraphs pick up, and '[.small]' has no effect.
# The index is typeset the same way, from the ambient font and the
# 'description_list_*' spacing keys.  This extension restores that control for
# both structures when they carry the 'compact' role, which the glossary and the
# index use for their long term-and-definition listings.
#
# A description list opts in by carrying the role alongside its style:
#
#   [glossary.compact]
#   Array::
#   A mutable, typed, contiguous sequence.
#
# and the index section by carrying it on the section:
#
#   [index.compact]
#   == Index
#
# Each structure is typeset at the 'font-size' of its own theme category,
# 'description-list: compact:' or 'index: compact:', which accepts either an
# absolute size in points or a relative size such as '0.85em'.  Any other
# 'compact' keys in that category are applied over their plain counterparts for
# the duration of the structure, so the treatment can be tuned from
# tiri-theme.yml without editing this file.  For example:
#
#   description-list:
#     compact:
#       font-size: 0.85em
#       term-spacing: 2
#
#   index:
#     compact:
#       font-size: 0.85em
#       columns: 3
#
# Codespans inherit the reduced size automatically because 'codespan font-size'
# is expressed in em, and is therefore relative to the enclosing text.
#
# Without a 'font-size' key the role falls back to DEFAULT_FONT_SIZE of the font
# size that is otherwise in effect.
#
# Usage with Asciidoctor:
#   asciidoctor-pdf -r ./tiri_compact_list.rb document.adoc

require 'asciidoctor/pdf'

module Asciidoctor
   module PDF
      module TiriCompactList
         DEFAULT_FONT_SIZE = '0.85em'

         def convert_dlist node
            return super unless node.has_role? 'compact'
            with_compact_theme('description_list') { super }
         end

         def convert_index_section node
            return super unless node.has_role? 'compact'
            with_compact_theme('index') { super }
         end

         private

         # Typeset the enclosed structure at the compact size of the given theme category,
         # with the remaining compact keys of that category in effect.
         def with_compact_theme category, &block
            overrides = compact_theme_overrides_for category
            saved = {}
            overrides.each_key {|key| saved[key] = @theme[key] }
            overrides.each {|key, value| @theme[key] = value }
            begin
               font_size(@theme[%(#{category}_compact_font_size)] || DEFAULT_FONT_SIZE, &block)
            ensure
               saved.each {|key, value| @theme[key] = value }
            end
         end

         # Map the '<category>_compact_*' theme keys onto their '<category>_*' counterparts.
         # The prefix is stripped rather than matched against a fixed list, so nested keys
         # such as 'description_list_compact_term_font_style' resolve to
         # 'description_list_term_font_style'.  'font_size' is excluded because it is applied
         # to the structure as a whole rather than to a single category.
         def compact_theme_overrides_for category
            marker = %(#{category}_compact_)
            size_key = %(#{marker}font_size)
            (@tiri_compact_overrides ||= {})[category] ||= @theme.each_pair.each_with_object({}) do |(key, value), accum|
               next unless (key.to_s.start_with? marker) && key.to_s != size_key
               accum[%(#{category}_#{(key.to_s.slice marker.length, key.length)})] = value
            end
         end
      end

      Converter.prepend TiriCompactList
   end
end
