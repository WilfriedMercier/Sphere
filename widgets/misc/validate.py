#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Wilfried Mercier - IRAP

Miscellaneous fonctions which can used at any point throughout the program
"""

def validateType(data, typ):
    '''
    Validate (or invalidate) user text content, specifically its data type.'''
    
    if not isinstance(data, typ):
        try:
            data = typ(data)
            return True
        except ValueError:
            pass
    else:
        return True
    
    return False

# Aliases for simple data types

def validateFloat(data):
    return validateType(data, float)

def validateInt(data):
    return validateType(data, int)

def validateStr(data):
    return validateType(data, str)

def validateList(data):
    return validateType(data, list)

