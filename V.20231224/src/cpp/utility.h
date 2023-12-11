#pragma once
#include <string>
#include <string.h>
#include <vector>
#include <sstream>
#include <ctime>

// Namespace utility contains utility functions for string manipulation and time conversion.
namespace utility {

    // Time format used by Interactive Brokers (IB).
    #define IB_TIME_FMT "%Y%m%d %H:%M:%S"

    // Converts a string to time_t using the specified format.
    inline time_t to_time_t(const std::string &s, const char *fmt = IB_TIME_FMT) {
        return to_time_t(s.c_str(), fmt);
    }

    // Converts a C-style string to time_t using the specified format.
    inline time_t to_time_t(const char *s, const char *fmt = IB_TIME_FMT) {
        struct tm timeptr;
        memset(&timeptr, 0, sizeof(timeptr));
        strptime(s, fmt, &timeptr);
        return timelocal(&timeptr);
    }

    // Converts time_t to a string using the specified format.
    inline std::string to_time_str(time_t t, const char *fmt = IB_TIME_FMT) {
        struct tm timeptr;
        memset(&timeptr, 0, sizeof(timeptr));
        localtime_r(&t, &timeptr);
        std::string sz(64, '\0');
        strftime(sz.data(), sz.size(), fmt, &timeptr);
        sz.resize(strlen(sz.data()));
        return sz;
    }

    // String containing whitespace characters.
    const std::string WHITESPACE = " \n\r\t\f\v";

    // Trims leading whitespace from a string.
    inline std::string ltrim(const std::string &s) {
        size_t start = s.find_first_not_of(WHITESPACE);
        return (start == std::string::npos) ? "" : s.substr(start);
    }

    // Trims trailing whitespace from a string.
    inline std::string rtrim(const std::string &s) {
        size_t end = s.find_last_not_of(WHITESPACE);
        return (end == std::string::npos) ? "" : s.substr(0, end + 1);
    }

    // Trims both leading and trailing whitespace from a string.
    inline std::string trim(const std::string &s) {
        return rtrim(ltrim(s));
    }

    // Splits a string into a vector of strings based on a delimiter character.
    // Optionally removes empty strings and trims each substring.
    inline std::vector<std::string> strSplit(std::string str, const char delim, bool removeEmpty = false, bool strip = true) {
        std::vector<std::string> ret;
        std::istringstream ss(str);
        std::string v;
        while (getline(ss, v, delim)) {
            v = strip ? trim(v) : v;
            if (removeEmpty && v.empty()) {
                continue;
            }
            ret.push_back(v);
        }
        return ret;
    }
};
