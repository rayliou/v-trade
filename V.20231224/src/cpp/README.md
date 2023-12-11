- 3rd party source

# Setup the correct version of clang
```
sudo apt install -y clang-15  clang-format  clang-tools-15  clangd-15 cmake unzip fd-find ripgrep
sudo update-alternatives --install /usr/bin/cc cc /usr/bin/clang-15 100
sudo update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-15 100
sudo update-alternatives --config cc
sudo update-alternatives --config c++
cc --version
c++ --version
```
#  Intel(R) Decimal Floating-Point Math Library
- https://www.intel.com/content/www/us/en/developer/articles/tool/intel-decimal-floating-point-math-library.html
- https://www.netlib.org/misc/intel/