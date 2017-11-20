# -*- coding: utf-8 -*-
import pypandoc
pypandoc.convert(
    source='README.md',
    format='markdown_github',
    to='rst',
    outputfile='README.rst')
