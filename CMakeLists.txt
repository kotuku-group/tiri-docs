# Tiri documentation

set (TIRI_REFERENCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/tiri-reference")
set (TIRI_REFERENCE_PDF "${CMAKE_CURRENT_SOURCE_DIR}/pdf/tiri-reference.pdf")
set (TIRI_REFERENCE_HTML_DIR "${CMAKE_CURRENT_SOURCE_DIR}/html")
set (TIRI_REFERENCE_HTML "${TIRI_REFERENCE_HTML_DIR}/index.html")
set (TIRI_REFERENCE_HTML_ASSETS "${TIRI_REFERENCE_HTML_DIR}/.images-copied")

find_program (ASCIIDOCTOR_EXECUTABLE NAMES asciidoctor)
find_program (ASCIIDOCTOR_PDF_EXECUTABLE NAMES asciidoctor-pdf)
find_program (PYTHON3_EXECUTABLE NAMES python3)

file (GLOB TIRI_REFERENCE_CHAPTER_SOURCES CONFIGURE_DEPENDS
   "${TIRI_REFERENCE_DIR}/ch[0-9][0-9]_*.adoc"
   "${TIRI_REFERENCE_DIR}/appendix_*.adoc")

# ch33_tiri_lsp.adoc is not part of book.adoc until its reference content is complete.
list (REMOVE_ITEM TIRI_REFERENCE_CHAPTER_SOURCES "${TIRI_REFERENCE_DIR}/ch33_tiri_lsp.adoc")

file (GLOB_RECURSE TIRI_REFERENCE_COMMON_SOURCES CONFIGURE_DEPENDS
   "${TIRI_REFERENCE_DIR}/*.rb"
   "${TIRI_REFERENCE_DIR}/*.yml"
   "${TIRI_REFERENCE_DIR}/images/*"
   "${CMAKE_CURRENT_SOURCE_DIR}/fonts/*")

set (TIRI_REFERENCE_PDF_SOURCES
   "${TIRI_REFERENCE_DIR}/book.adoc"
   "${TIRI_REFERENCE_DIR}/front-matter.adoc"
   ${TIRI_REFERENCE_CHAPTER_SOURCES}
   ${TIRI_REFERENCE_COMMON_SOURCES})

file (GLOB_RECURSE TIRI_REFERENCE_HTML_DOCUMENT_SOURCES CONFIGURE_DEPENDS
   "${TIRI_REFERENCE_DIR}/*.adoc"
   "${TIRI_REFERENCE_DIR}/*.css"
   "${TIRI_REFERENCE_DIR}/*.html")

set (TIRI_REFERENCE_HTML_SOURCES
   ${TIRI_REFERENCE_HTML_DOCUMENT_SOURCES}
   ${TIRI_REFERENCE_COMMON_SOURCES})

set (TIRI_REFERENCE_CHAPTER_HTML_OUTPUTS)
foreach (TIRI_REFERENCE_CHAPTER_SOURCE IN LISTS TIRI_REFERENCE_CHAPTER_SOURCES)
   get_filename_component (TIRI_REFERENCE_CHAPTER_NAME "${TIRI_REFERENCE_CHAPTER_SOURCE}" NAME_WE)
   list (APPEND TIRI_REFERENCE_CHAPTER_HTML_OUTPUTS "${TIRI_REFERENCE_HTML_DIR}/${TIRI_REFERENCE_CHAPTER_NAME}.html")
endforeach ()

set (TIRI_REFERENCE_OUTPUTS)

if (ASCIIDOCTOR_PDF_EXECUTABLE)
   add_custom_command (
      OUTPUT "${TIRI_REFERENCE_PDF}"
      COMMAND "${ASCIIDOCTOR_PDF_EXECUTABLE}"
         -a source-highlighter=rouge
         -o "${TIRI_REFERENCE_PDF}"
         -r ./tiri_lexer.rb
         -r ./tiri_compact_toc.rb
         -r ./tiri_ebnf.rb
         -r ./tiri_compact_table.rb
         -r ./tiri_compact_list.rb
         book.adoc
      WORKING_DIRECTORY "${TIRI_REFERENCE_DIR}"
      DEPENDS ${TIRI_REFERENCE_PDF_SOURCES}
      COMMENT "Building the Tiri Reference Manual PDF"
      VERBATIM)

   list (APPEND TIRI_REFERENCE_OUTPUTS "${TIRI_REFERENCE_PDF}")
else ()
   message (STATUS "asciidoctor-pdf was not found; PDF output for the Tiri Reference Manual will be unavailable.")
endif ()

if (ASCIIDOCTOR_EXECUTABLE AND PYTHON3_EXECUTABLE)
   add_custom_command (
      OUTPUT "${TIRI_REFERENCE_HTML_ASSETS}"
      COMMAND "${CMAKE_COMMAND}" -E make_directory "${TIRI_REFERENCE_HTML_DIR}"
      COMMAND "${CMAKE_COMMAND}" -E copy_directory
         "${TIRI_REFERENCE_DIR}/images" "${TIRI_REFERENCE_HTML_DIR}/images"
      COMMAND "${CMAKE_COMMAND}" -E copy_if_different
         "${TIRI_REFERENCE_DIR}/chapter-navigation.html" "${TIRI_REFERENCE_HTML_DIR}/chapter-navigation.html"
      COMMAND "${CMAKE_COMMAND}" -E copy_if_different
         "${TIRI_REFERENCE_DIR}/chapter-navigation.css" "${TIRI_REFERENCE_HTML_DIR}/chapter-navigation.css"
      COMMAND "${CMAKE_COMMAND}" -E copy_if_different
         "${TIRI_REFERENCE_DIR}/index-title.css" "${TIRI_REFERENCE_HTML_DIR}/index-title.css"
      COMMAND "${CMAKE_COMMAND}" -E touch "${TIRI_REFERENCE_HTML_ASSETS}"
      DEPENDS ${TIRI_REFERENCE_HTML_SOURCES}
      COMMENT "Staging the Tiri Reference Manual HTML assets"
      VERBATIM)

   add_custom_command (
      OUTPUT "${TIRI_REFERENCE_HTML}"
      COMMAND "${ASCIIDOCTOR_EXECUTABLE}"
         -a docinfo=shared,private
         -a source-highlighter=rouge
         -o "${TIRI_REFERENCE_HTML}"
         -r ./tiri_lexer.rb
         -r ./tiri_compact_toc.rb
         -r ./tiri_ebnf.rb
         -r ./tiri_compact_table.rb
         -r ./tiri_compact_list.rb
         index.adoc
      WORKING_DIRECTORY "${TIRI_REFERENCE_DIR}"
      DEPENDS ${TIRI_REFERENCE_HTML_SOURCES} "${TIRI_REFERENCE_HTML_ASSETS}"
      COMMENT "Building the Tiri Reference Manual HTML"
      VERBATIM)

   list (APPEND TIRI_REFERENCE_OUTPUTS "${TIRI_REFERENCE_HTML}")

   add_custom_command (
      OUTPUT ${TIRI_REFERENCE_CHAPTER_HTML_OUTPUTS}
      COMMAND "${PYTHON3_EXECUTABLE}" "${TIRI_REFERENCE_DIR}/build_chapters.py"
         --backend html --output "${TIRI_REFERENCE_HTML_DIR}"
      WORKING_DIRECTORY "${TIRI_REFERENCE_DIR}"
      DEPENDS "${TIRI_REFERENCE_DIR}/build_chapters.py" ${TIRI_REFERENCE_HTML_SOURCES}
         "${TIRI_REFERENCE_HTML_ASSETS}"
      COMMENT "Building the Tiri Reference Manual chapter HTML"
      VERBATIM)

   list (APPEND TIRI_REFERENCE_OUTPUTS ${TIRI_REFERENCE_CHAPTER_HTML_OUTPUTS})
else ()
   message (STATUS "asciidoctor or python3 was not found; HTML output for the Tiri Reference Manual will be unavailable.")
endif ()

if (TIRI_REFERENCE_OUTPUTS)
   add_custom_target (tiri_reference_manual
      DEPENDS ${TIRI_REFERENCE_OUTPUTS})
else ()
   message (STATUS "No Asciidoctor executable was found; the Tiri Reference Manual target will be unavailable.")
endif ()
