#!/bin/bash
#
# Copyright (C) 2017 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Generates mojo sources given a list of .mojom files and args.
# Usage: $0 --mojom_bindings_generator=<abs_path> --package=<package_directory>
#            --output_dir=<output_directory>
#            [<extra_args_for_bindings_generator>] <list_of_mojom_files>

set -e

args=()
files=()
includes=()
gen_dirs=()

mojom_bindings_generator=""
package=""
output_dir=""
generators=""

# Given a path to directory or file, return the absolute path.
get_abs_path() {
  if [[ -d $1 ]] ; then
    cd "$1"
    filename=""
  else
    filepath=$1
    dir="${filepath%/*}"
    cd "${dir}"
    filename="${filepath#${dir}/}"
  fi
  absdir=`pwd`
  cd - > /dev/null
  echo "${absdir}/${filename}"
}

for arg in "$@"; do
  case "${arg}" in
    --mojom_bindings_generator=*)
      mojom_bindings_generator="${arg#'--mojom_bindings_generator='}"
      mojom_bindings_generator="$(get_abs_path ${mojom_bindings_generator})"
      ;;
    --package=*)
      package="${arg#'--package='}"
      ;;
    --output_dir=*)
      output_dir="${arg#'--output_dir='}"
      output_dir="$(get_abs_path ${output_dir})"
      ;;
    --typemap=*)
      typemap="${arg#'--typemap='}"
      typemap="$(get_abs_path ${typemap})"
      args+=("--typemap=${typemap}")
      ;;
    --bytecode_path=*)
      bytecode_path="${arg#'--bytecode_path='}"
      bytecode_path="$(get_abs_path ${bytecode_path})"
      ;;
    --generators=*)
      generators="${arg#'--generators='}"
      ;;
    --srcjar=*)
      srcjar="${arg#'--srcjar='}"
      srcjar="$(get_abs_path ${srcjar})"
      ;;
    -I=*)
      includes+=("$(get_abs_path "${arg#'-I='}")")
      ;;
    --*)
      args+=("${arg}")
      ;;
    *.mojom)
      # Add all .mojom files directly as files.
      files+=("$(get_abs_path ${arg})")
      ;;
    *.p)
      # Get the gen/ dir of any pickle (.p) file so that the bindings
      # generator
      # can get the correct path.
      gen_dirs+=("$(get_abs_path "${arg}" | sed -e 's@/gen/.*$@/gen@')")
  esac
done

# Add the current package as include path, and then rewrite all the include
# paths so that the bindings generator can relativize the paths correctly.
includes+=("$(pwd)/${package}")
includes=($(printf -- "%q\n" "${includes[@]}" | sed -e 's/.*/-I=&:&/'))

# Remove duplicates from the list of gen/ directories that contain the pickle
# files.
if [[ "${#gen_dirs[@]}" -ge 1 ]]; then
  gen_dirs=($(printf -- "--gen_dir=%q\n" "${gen_dirs[@]}" | sort -u))
fi

"${mojom_bindings_generator}" --use_bundled_pylibs precompile \
    -o "${output_dir}"

for file in "${files[@]}"; do
  # Java source generations depends on zipfile that assumes the output directory
  # already exists. So, we need to create the directory beforehand.
  rel_path="${file#`pwd`/$package/}"
  rel_dir="${rel_path%/*}"

  mkdir -p "${output_dir}/${rel_dir}"

  "${mojom_bindings_generator}" --use_bundled_pylibs generate \
      -o "${output_dir}" "${args[@]}" \
      --bytecode_path="${bytecode_path}" \
      "${gen_dirs[@]}" \
      -d "${package}" \
      "${includes[@]}" \
      --generators="${generators}" "${file}"
  if [[ "${generators}" =~ .*c\+\+.* ]] ; then
    "${mojom_bindings_generator}" --use_bundled_pylibs generate \
        -o "${output_dir}" \
        --generate_non_variant_code "${args[@]}" \
        "${gen_dirs[@]}" \
        -d "${package}" \
        "${includes[@]}" \
        --bytecode_path="${bytecode_path}" --generators="${generators}" \
        "${file}"
  fi
  if [[ "${generators}" =~ .*java.* ]] ; then
    unzip -qo -d "${output_dir}"/src "${output_dir}/${rel_path}".srcjar
  fi
done

if [[ -n "${srcjar}" ]] ; then
  (cd "${output_dir}/src" && \
   find . -name '*.java' -print | zip --quiet "${srcjar}" -@)
fi
