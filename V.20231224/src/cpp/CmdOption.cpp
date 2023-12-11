#include "CmdOption.h"

CmdOption::CmdOption(int argc, char *argv[]) : m_argc(argc), m_argv(argv) {}

char *CmdOption::get(const std::string &option) {
    auto begin = m_argv;
    auto end = m_argv + m_argc;
    return _get(option, begin, end);
}

std::vector<std::string> CmdOption::getM(const std::string &option) {
    std::vector<std::string> ret;
    auto begin = m_argv;
    auto end = m_argv + m_argc;
    char **last = begin;
    char *s;
    while (nullptr != (s = _get(option, last, end, &last))) {
        ret.push_back(s);
    }
    return ret;
}

bool CmdOption::exists(const std::string &option) {
    auto begin = m_argv;
    auto end = m_argv + m_argc;
    char **itr = std::find(begin, end, option);
    return itr != end;
}

std::string CmdOption::str() const {
    std::ostringstream ss;
    for (auto it = m_argv; it != m_argv + m_argc; it++) {
        ss << (*it);
        ss << " ";
    }
    return ss.str();
}

char *CmdOption::_get(const std::string &option, char **begin, char **end,
                      char ***last) {
    char **itr = std::find(begin, end, option);
    if (itr != end && ++itr != end) {
        if (nullptr != last) {
            *last = itr + 1;
        }
        return *itr;
    }
    return nullptr;
}
