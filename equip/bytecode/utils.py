# -*- coding: utf-8 -*-
"""
  equip.bytecode.utils
  ~~~~~~~~~~~~~~~~~~~~

  Utilities for bytecode interaction.

  :copyright: (c) 2014 by Romain Gaucher (@rgaucher)
  :license: Apache 2, see LICENSE for more details.
"""
import opcode
import types
import dis
from ..utils.log import logger


def iter_decl(decl):
  """
    Yield declarations that are nested under the given declaration.

    :param decl: The root ``Declaration`` to visit.
  """
  try:
    worklist = [decl]
    while worklist:
      decl = worklist.pop(0)
      yield decl
      children = decl.children
      for child in children:
        worklist.insert(0, child)
  except StopIteration, ex:
    pass


# Look into the main_co if we get orignal_co, if so we replace it with new_co
def update_nested_code_object(main_co, original_co, new_co):
  if not main_co:
    return
  logger.debug("Looking in main %s, replace by %s" % (original_co, new_co))

  main_co_consts = main_co.co_consts
  co_index = -1
  for co_const in main_co_consts:
    if not isinstance(co_const, types.CodeType):
      continue
    if co_const == original_co:
      co_index = main_co_consts.index(co_const)
      break

  if co_index < 0:
    logger.debug("Cannot find %s in main_co: %s" % (original_co, main_co_consts))
    return main_co

  new_co_consts = main_co.co_consts[:co_index] + (new_co,) + main_co.co_consts[co_index + 1:]
  main_co = types.CodeType(main_co.co_argcount, main_co.co_nlocals,
                           main_co.co_stacksize, main_co.co_flags,
                           main_co.co_code, new_co_consts,
                           main_co.co_names, main_co.co_varnames,
                           main_co.co_filename, main_co.co_name,
                           main_co.co_firstlineno, main_co.co_lnotab,
                           main_co.co_freevars, main_co.co_cellvars)

  logger.debug("Created new CO: %s" % main_co)
  return main_co


def show_bytecode(bytecode, start=0, end=2**32):
  from ..analysis.python.effects import get_stack_effect

  if bytecode is None:
    return ''
  buffer = []
  j = start
  end = min(end, len(bytecode) - 1)
  while j <= end:
    index, lineno, op, arg, _, co = bytecode[j]
    uid = hex(id(co))[-5:]

    pop_push_str = ''
    try:
      pop, push = get_stack_effect(op, arg)
      pop_push_str = ' (-%d +%d) ' % (pop, push)
    except ValueError, ex:
      pop_push_str = '         '

    if op >= opcode.HAVE_ARGUMENT:
      rts = repr(arg)
      if len(rts) > 40:
        rts = rts[:40] + '[...]'
      jump_target = ''
      if op in opcode.hasjrel or op in opcode.hasjabs:
        jump_address = arg if op in opcode.hasjabs else index + arg + 3
        jump_target = ' -------------> (%4d)' % jump_address

      buffer.append("[%5s]%4d(%4d) %20s(%3d)%s (%s)%s"
                    % (uid, lineno, index, opcode.opname[op], op, pop_push_str, rts, jump_target))
    else:
      buffer.append("[%5s]%4d(%4d) %20s(%3d)%s"
                    % (uid, lineno, index, opcode.opname[op], op, pop_push_str))
    j += 1
  return '\n'.join(buffer)


CO_FIELDS = ('co_argcount', 'co_cellvars', 'co_consts', 'co_filename',
             'co_firstlineno', 'co_flags', 'co_freevars', 'co_lnotab', 'co_name',
             'co_names', 'co_nlocals', 'co_stacksize', 'co_varnames')


def get_debug_code_object_info(code_object):
  buffer = []
  for field in CO_FIELDS:
    field_name = field.replace('co_', '')
    val = getattr(code_object, field)
    buffer.append("%s := %s" % (field_name, val))
  return '\n'.join(buffer)


def get_debug_code_object_dict(code_object):
  dct = {}
  for field in CO_FIELDS:
    val = getattr(code_object, field)
    dct[field] = val
  return dct

