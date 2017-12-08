# clinto
[![Build Status](https://travis-ci.org/wooey/clinto.svg)](https://travis-ci.org/wooey/clinto)
[![Coverage Status](https://coveralls.io/repos/wooey/clinto/badge.svg?branch=master&service=github)](https://coveralls.io/github/wooey/clinto?branch=master)

[![Join the chat at https://gitter.im/wooey/clinto](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/wooey/clinto?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This converts an assortment of python command line interfaces into a language agnostic build spec for usage in GUI creation.

Here's a basic usage:
```
from clinto import parser
specs = parser.Parser(script_path='/home/chris/Devel/pythomics/pythomics/scripts/proteinInference.py', script_name='Protein Inference')
specs.get_script_description()
{
  'name': 'Protein Inference Script',
  'path': '/home/chris/Devel/pythomics/pythomics/scripts/proteinInference.py'
  'description': '\nThis script will annotate a tab delimited text file with peptides with\ncorresponding proteins present in an annotation file, and can also\nuse this annotation to include iBAQ measures.\n',
  'inputs': {
    'parser_name': [{
      'group': 'optional arguments',
      'nodes': [{
          'choice_limit': None,
          'choices': None,
          'help': 'Threads to run',
          'model': 'IntegerField',
          'name': 'p',
          'param': '-p',
          'required': False,
          'type': 'text',
          'value': 1
        }, {
          'choice_limit': '1',
          'choices': None,
          'help': 'The fasta file to match peptides against.',
          'model': 'FileField',
          'name': 'fasta',
          'param': '-f',
          'required': False,
          'type': 'file',
          'upload': True
        }],
      },
      'group': 'Protein Grouping Options',
      'nodes': [{
          'checked': False,
          'choice_limit': 0,
          'choices': None,
          'help': 'Only group proteins with unique peptides',
          'model': 'BooleanField',
          'name': 'unique_only',
          'param': '--unique-only',
          'required': False,
          'type': 'checkbox'
        }, {
          'checked': False,
          'choice_limit': 0,
          'choices': None,
          'help': 'Write the position of the peptide matches.',
          'model': 'BooleanField',
          'name': 'position',
          'param': '--position',
          'required': False,
          'type': 'checkbox'
        }],
     ]
   },
}
```
