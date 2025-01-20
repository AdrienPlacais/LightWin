# Makefile for Sphinx documentation

SPHINXOPTS    ?=
# Builders
SPHINXBUILD   ?= sphinx-build
SPHINXAPIDOC  ?= sphinx-apidoc
# Dirs
SOURCEDIR     = .
BUILDDIR      = ../../_tmp_LightWin-docs
SRC_DIR       = ../src
EXCLUDE_DIR   = ../src/lightwin/experimental/*
APIDOC_DIR    = lightwin
CONFIG_ENTRIES_DIR = manual/configuration_entries

GENERATE_CSV  = scripts/generate_config_csv.py

.PHONY: help clean apidoc generate_csv html 

# Default target: help
.DEFAULT_GOAL := help

help:
	@echo "Usage: make [TARGET]"
	@echo ""
	@echo "Available targets:"
	@echo "  help            Show this help message"
	@echo "  clean           Clean build artifacts"
	@echo "  apidoc          Generate API documentation"
	@echo "  generate_csv    Generate CSV configuration files"
	@echo "  html            Build unversioned HTML documentation"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf "$(BUILDDIR)"
	@if [ -d "$(APIDOC_DIR)" ]; then rm -rf "$(APIDOC_DIR)"/*; fi
	@if [ -d "$(CONFIG_ENTRIES_DIR)" ]; then rm -rf "$(CONFIG_ENTRIES_DIR)"/*; fi
	@if [ -d "$(MULTIVERSION_OUTPUT)" ]; then \
	  find "$(MULTIVERSION_OUTPUT)" -mindepth 1 ! -name 'index.html' -exec rm -rf {} +; \
	fi

# Generate API documentation using sphinx-apidoc
apidoc:
	@echo "Generating API documentation..."
	@$(SPHINXAPIDOC) -o "$(APIDOC_DIR)" -d 5 -f -e -M "$(SRC_DIR)" "$(EXCLUDE_DIR)"
	@cd "$(APIDOC_DIR)" && perl -i -pe 's/^\S*\.(\S*) (package|module)/$$1 $$2/' *.rst

# Generate CSV for configuration documentation
generate_csv:
	@echo "Generating CSV configuration files..."
	@python "$(GENERATE_CSV)"

# Build unversioned HTML documentation
html:
	@echo "Building unversioned HTML documentation..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new "make mode" option
%:
	@echo "Unknown target '$@'."
	@$(MAKE) help
