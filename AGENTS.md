# AGENTS.md - Guidelines for AI Agents Working on DEVSIM

This document provides guidelines for AI agents working on the DEVSIM TCAD device simulator codebase.

## Project Overview

DEVSIM is a TCAD Device Simulator using finite volume methods. It's primarily written in C++ (C++17) with Python scripting support and CMake as the build system.

- **Language**: C++17 with Python bindings
- **Build System**: CMake
- **License**: Apache 2.0
- **Website**: https://devsim.org

## Build Commands

### Setup (First Time)
```bash
git submodule init
git submodule update
```

### Build
```bash
mkdir build && cd build
cmake .. -DDEVSIM_CONFIG=<config>  # e.g., ubuntu_18.04, osx_gcc, msys, etc.
make -j$(nproc)
```

Common CMake options:
- `DEVSIM_CONFIG`: Platform config from cmake/ directory
- `PYTHON3=ON` (default): Build Python 3 interpreter
- `MKL_PARDISO=ON` (default): Use Intel MKL Pardiso solver
- `DEVSIM_EXTENDED_PRECISION=OFF` (default): Extended floating point precision

### Running Tests

Run all tests:
```bash
cd build
ctest
```

Run a single test:
```bash
ctest -R "testing/info"        # Run specific test by name pattern
ctest -V -R "testing/cap2"     # Run with verbose output
```

Run tests with specific Python executable:
```bash
ctest -D DEVSIM_PY3_TEST_EXE=/path/to/python
```

### Pre-commit Hooks (Formatting)

Install and run formatting:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Or manually format Python:
```bash
ruff check --fix .
ruff format .
```

## Code Style Guidelines

### C++ Code Style

Based on `.clang-format` (Google style variant):

- **Indent**: 2 spaces
- **Line length**: 80 columns
- **Braces**: 
  - Functions: newline after (K&R style)
  - Control statements: same line
  - Classes: same line
- **Pointer alignment**: Left (`int* ptr` not `int *ptr`)
- **Namespaces**: No indentation
- **Short functions**: Can be on single line if ≤ 1 statement
- **Include order**: Do not sort includes (SortIncludes: Never)

Example:
```cpp
class MyClass {
 public:
  void ShortFunc() { return; }
  
  void LongerFunction() {
    if (condition) {
      DoSomething();
    } else {
      DoOtherThing();
    }
  }
};
```

### Python Code Style

Based on `ruff.toml` (Black-compatible):

- **Indent**: 4 spaces
- **Line length**: 88 columns
- **Quotes**: Double quotes preferred
- **Target**: Python 3.7+

### File Headers

All files must include Apache 2.0 license header:

C++:
```cpp
/***
DEVSIM
Copyright 20XX DEVSIM LLC

SPDX-License-Identifier: Apache-2.0
***/
```

Python:
```python
# Copyright 20XX DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0
```

### Naming Conventions

- **C++ Classes**: PascalCase (e.g., `CommandHandler`, `EdgeModel`)
- **C++ Functions**: camelCase (e.g., `getParameter`, `setValue`)
- **C++ Private members**: trailing underscore (e.g., `command_info_`)
- **C++ Constants**: UPPER_SNAKE_CASE or kCamelCase
- **Python**: snake_case for functions and variables
- **File names**: PascalCase for C++ headers (.hh), lowercase for Python

### Project Structure

```
src/
  adiff/          # Automatic differentiation
  AutoEquation/   # Equation automation
  Circuit/        # Circuit simulation
  commands/       # Command implementations
  common_api/     # Shared API interfaces
  Data/           # Global data management
  Equation/       # Equation system
  errorSystem/    # Error handling
  Geometry/       # Mesh geometry
  GeomModels/     # Geometry models
  main/           # Main entry point
  math/           # Math utilities
  MathEval/       # Math evaluation
  meshing/        # Mesh generation
  models/         # Physical models
  old/            # Legacy code
  pythonapi/      # Python bindings
  utility/        # Utilities

testing/          # Regression tests
examples/         # Example simulations
cmake/            # CMake configurations
```

## Error Handling

- Use `dsAssert()` for assertions (from `dsAssert.hh`)
- Use `errorSystem` for user-facing errors
- Commands should use `CommandHandler::SetErrorResult()` for errors
- Prefer exceptions for exceptional conditions, error codes for expected failures

## Testing Guidelines

- Tests are Python scripts in `testing/` directory
- Tests compare output against golden results in `goldenresults/`
- Use `rundifftest.py` for running tests with output comparison
- Tests have dependencies (e.g., restart tests depend on initial run)
- Golden results are platform-specific due to compiler/math library differences

## Pre-commit Requirements

All code must pass:
1. **Ruff linting** (`ruff check`)
2. **Ruff formatting** (`ruff format`)
3. **clang-format** (for C++ files)

Install hooks: `pre-commit install`
Run manually: `pre-commit run --all-files`

## Version Management

Version is set in root `CMakeLists.txt`:
- `DEVSIM_VERSION_STRING` (e.g., "2.10.0")
- `DEVSIM_COPYRIGHT_YEAR` (e.g., "2009-2025")

## Important Notes

- Do not modify `external/` or `umfpack/` directories (excluded from formatting)
- SortIncludes is disabled in clang-format - maintain existing include order
- Tests are in separate repositories (see TEST.md for links)
- The codebase uses custom smart pointer patterns in many places
