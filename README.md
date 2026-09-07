# Tiri Documentation

Official documentation for the Tiri programming language.

## Build the Manuals

This project is intended to be installed as a submodule of the Kōtuku framework in `docs/tiri`, and is not maintained as an independent project.

Building the HTML manual requires Asciidoctor and Rouge.  PDF output additionally requires Asciidoctor PDF.  Install the
required Ruby gems before configuring the project:

```sh
gem install asciidoctor asciidoctor-pdf rouge
```

Configure Kōtuku as normal.  Building the documentation requires explicit targeting from the repository root:

```sh
cmake --build <build_folder> --target tiri_reference_manual
```

Generated PDFs are written to `docs/tiri/pdf/`.  HTML output is written to `docs/tiri/html/`, with the complete manual
in `index.html` and each chapter and appendix in a separate HTML file.  Images are copied to `html/images/`.
If either generator is not available when CMake is configured, its output is omitted; install the missing dependency and
reconfigure the build tree.

# Licensing

All files remain the sole copyright of Paul Manias unless otherwise specified.

The re-distribution of these files or content generated from them is prohibited.  For publicly distributable electronic PDFs, please download them directly from our Git repository or website.
