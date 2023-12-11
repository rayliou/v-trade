#pragma once
#include <algorithm>
#include <sstream>
#include <string>
#include <vector>

class CmdOption {
  public:
    // Constructor: Initializes the command option with argument count and
    // argument values.
    CmdOption(int argc, char *argv[]);

    // Retrieves the value associated with a given option.
    char *get(const std::string &option);

    // Retrieves multiple values associated with a given option.
    std::vector<std::string> getM(const std::string &option);

    // Checks if a given option exists in the arguments.
    bool exists(const std::string &option);

    // Converts the command line arguments to a single string.
    std::string str() const;

  private:
    // Helper function to retrieve a single argument associated with a given
    // option.
    char *_get(const std::string &option, char **begin, char **end,
               char ***last = nullptr);

  private:
    int m_argc;    // Argument count
    char **m_argv; // Argument values
};
