# Biometalib

Biometalib is a set of useful libraries and tools for working with SRA biological metadata.

## Installation

This library is designed for python 3+ and can be installed with `pip` or `conda`.

### Pip

If using pip you must first install my `sramongo` package.

```bash
pip install git+https://github.com/jfear/sramongo
pip install git+https://github.com/jfear/biometalib
```

### Conda [Suggested]

First make sure you have a working installation of Anaconda, I suggest
[Miniconda](https://conda.io/miniconda.html).

```bash
conda install -c jfear biometalib
```

## Attribute Selector

Attribute selector is a helper script for selecting which attributes you want
to focus on for a project. The biological metadata submitted by users contain a
variety of different types of attributes. Sometimes these include things like
misspellings or different forms of a word, it also includes attributes that are
unique to a single project. This tool is to be used to quickly curate these
columns. Attribute selector uses a `YAML` formatted file to store attribute
decisions.

In the YAML file, **selected attributes** will be the keys. When merging
multiple attributes into a single **selected attribute** they will be stored as
values. For example:

```
sex:
- sex
- Sex
- gender
```

Here the **selected attribute** `sex` has the attributes `Sex` and `gender`
associated with it.  There is also a special **selected attribute** `ignore` that will store a list
of attributes that you want to ignore.

Using the BioSample selection sheet I have created a starting YAML that can be
used when running `attribute_selector`.

To run the attributes selector on my public version of the Biometa database type:

```bash
# Download example YAML
$ wget -O my_attribute_selection.yaml https://raw.githubusercontent.com/jfear/biometalib/master/data/flybase_example.yaml
$ attribute_selector --host mongo.geneticsunderground.com --port 27022 --db sra --username sra --password oliver --authenticationDatabase user-data --config my_attribute_selection.yaml
```

`attribute_selector` is an interactive command line tool. Iterates overall
attribute column names that are not already **selected attributes** in the
YAML. The current attribute is displayed in red. At the prompt you can type:

* `k` to set the current attribute as a **selected attribute** [keep]
* `r` to rename the current attribute, this will set the current attribute as
  value of the renamed **selected attribute** [rename]
* `i` adds current attribute to ignore list [ignore]
* `e` show example values listed under the current attribute [example]
* `s` show attributes with similar names (fuzzy string match). Here **selected attributes** will appear in yellow [similar]
* `n` skip and go to the next attribute [next]
* `quit` exit out of the program, but save progress.

