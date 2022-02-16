#pragma once
#include <string>
namespace utility {
    inline time_t strTime2time_t(const char *s, const char *fmt=nullptr) {
        const   char * TIME_FORMAT = "%Y-%m-%d %H:%M:%S";
        if (nullptr == fmt) {
            fmt = TIME_FORMAT;
        }
        struct tm timeptr;
        strptime(s,fmt,&timeptr);
        return mktime(&timeptr);
    }
    inline std::vector<std::string>  strSplit(std::string str, const char delim , bool removeEmpty =false) {
        std::vector<std::string> ret;
        std::istringstream ss(str);
        std::string v;
        while( getline(ss, v, delim)){
            if (removeEmpty && v == "" ) {
                continue;
            }
            ret.push_back(v);
        }
        return ret;
    }
    const std::string WHITESPACE = " \n\r\t\f\v";
    inline 
    std::string ltrim(const std::string &s) {
        size_t start = s.find_first_not_of(WHITESPACE);
        return (start == std::string::npos) ? "" : s.substr(start);
    }
    inline 
    std::string rtrim(const std::string &s) {
        size_t end = s.find_last_not_of(WHITESPACE);
        return (end == std::string::npos) ? "" : s.substr(0, end + 1);
    }
    inline 
    std::string trim(const std::string &s) { return rtrim(ltrim(s)); }
};

