# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: mobile_spa_registration.proto
# Protobuf Python Version: 5.28.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    2,
    '',
    'mobile_spa_registration.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dmobile_spa_registration.proto\x12\x13\x63om.levven.protobuf\"\x9f\x01\n\x17mobile_spa_registration\x12\x19\n\x11registration_code\x18\x01 \x01(\t\x12\x15\n\rserial_number\x18\x02 \x01(\t\x12\x14\n\x0cspa_nickname\x18\x03 \x01(\t\x12<\n\nreg_status\x18\x04 \x01(\x0e\x32(.com.levven.protobuf.REGISTRATION_STATUS*I\n\x13REGISTRATION_STATUS\x12\x18\n\x14REGISTRATION_SUCCESS\x10\x00\x12\x18\n\x14REGISTRATION_FAILURE\x10\x01')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'mobile_spa_registration_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_REGISTRATION_STATUS']._serialized_start=216
  _globals['_REGISTRATION_STATUS']._serialized_end=289
  _globals['_MOBILE_SPA_REGISTRATION']._serialized_start=55
  _globals['_MOBILE_SPA_REGISTRATION']._serialized_end=214
# @@protoc_insertion_point(module_scope)
