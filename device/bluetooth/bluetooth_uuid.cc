// Copyright 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "device/bluetooth/bluetooth_uuid.h"

#include <stddef.h>

#include "base/logging.h"
#include "base/strings/string_piece.h"
#include "base/strings/string_util.h"
#include "base/strings/utf_string_conversions.h"

#if defined(OS_WIN)
#include <objbase.h>

#include "base/strings/string16.h"
#endif  // defined(OS_WIN)

namespace device {

namespace {

const char kCommonUuidPostfix[] = "-0000-1000-8000-00805f9b34fb";
const char kCommonUuidPrefix[] = "0000";

// Returns the canonical, 128-bit canonical, and the format of the UUID
// in |canonical|, |canonical_128|, and |format| based on |uuid|.
void GetCanonicalUuid(std::string uuid,
                      std::string* canonical,
                      std::string* canonical_128,
                      BluetoothUUID::Format* format) {
  // Initialize the values for the failure case.
  canonical->clear();
  canonical_128->clear();
  *format = BluetoothUUID::kFormatInvalid;

  if (uuid.empty())
    return;

  if (uuid.size() < 11 &&
      base::StartsWith(uuid, "0x", base::CompareCase::SENSITIVE)) {
    uuid = uuid.substr(2);
  }

  if (!(uuid.size() == 4 || uuid.size() == 8 || uuid.size() == 36))
    return;

  for (size_t i = 0; i < uuid.size(); ++i) {
    if (i == 8 || i == 13 || i == 18 || i == 23) {
      if (uuid[i] != '-')
        return;
    } else {
      if (!base::IsHexDigit(uuid[i]))
        return;
      uuid[i] = base::ToLowerASCII(uuid[i]);
    }
  }

  canonical->assign(uuid);
  if (uuid.size() == 4) {
    canonical_128->assign(kCommonUuidPrefix + uuid + kCommonUuidPostfix);
    *format = BluetoothUUID::kFormat16Bit;
  } else if (uuid.size() == 8) {
    canonical_128->assign(uuid + kCommonUuidPostfix);
    *format = BluetoothUUID::kFormat32Bit;
  } else {
    canonical_128->assign(uuid);
    *format = BluetoothUUID::kFormat128Bit;
  }
}

}  // namespace


BluetoothUUID::BluetoothUUID(const std::string& uuid) {
  GetCanonicalUuid(uuid, &value_, &canonical_value_, &format_);
}

#if defined(OS_WIN)
BluetoothUUID::BluetoothUUID(GUID uuid) {
  // 36 chars for UUID + 2 chars for braces + 1 char for null-terminator.
  constexpr int kBufferSize = 39;
  wchar_t buffer[kBufferSize];
  int result = ::StringFromGUID2(uuid, buffer, kBufferSize);
  DCHECK_EQ(kBufferSize, result);
  if( ( L'{' != buffer[0] ) ||
      ( L'}' != buffer[37] ) )
  {
      LOG(ERROR) << "wrong char.";
  }

  GetCanonicalUuid(base::WideToUTF8(base::WStringPiece(buffer).substr(1, 36)),
                   &value_, &canonical_value_, &format_);
  DCHECK_EQ(kFormat128Bit, format_);
}
#endif  // defined(OS_WIN)

BluetoothUUID::BluetoothUUID() : format_(kFormatInvalid) {
}

BluetoothUUID::~BluetoothUUID() = default;

#if defined(OS_WIN)
// static
GUID BluetoothUUID::GetCanonicalValueAsGUID(base::StringPiece uuid) {
  DCHECK_EQ(36u, uuid.size());
  base::string16 braced_uuid = L'{' + base::UTF8ToWide(uuid) + L'}';
  GUID guid;
  CHECK_EQ(NOERROR, ::CLSIDFromString(braced_uuid.data(), &guid));
  return guid;
}
#endif  // defined(OS_WIN)

bool BluetoothUUID::IsValid() const {
  return format_ != kFormatInvalid;
}

bool BluetoothUUID::operator<(const BluetoothUUID& uuid) const {
  return canonical_value_ < uuid.canonical_value_;
}

bool BluetoothUUID::operator==(const BluetoothUUID& uuid) const {
  return canonical_value_ == uuid.canonical_value_;
}

bool BluetoothUUID::operator!=(const BluetoothUUID& uuid) const {
  return canonical_value_ != uuid.canonical_value_;
}

void PrintTo(const BluetoothUUID& uuid, std::ostream* out) {
  *out << uuid.canonical_value();
}

}  // namespace device
