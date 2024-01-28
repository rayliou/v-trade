#pragma once
#include <string>
#include <string.h>
namespace utility {

#define  IB_TIME_FMT  "%Y%m%d   %H:%M:%S"
    inline time_t to_time_t(const std::string &s, const char *fmt=IB_TIME_FMT ) { return to_time_t(s.c_str(),fmt); }
    inline time_t to_time_t(const char *s, const char *fmt=IB_TIME_FMT ) {
        struct tm timeptr;
        memset(&timeptr,0,sizeof(timeptr));
        strptime(s,fmt,&timeptr);
        return timelocal(&timeptr);
    }
    inline std::string to_time_str(time_t t, const char *fmt=IB_TIME_FMT ) {
        struct tm timeptr;
        memset(&timeptr,0,sizeof(timeptr));
        localtime_r(&t, &timeptr);
        std::string sz(64,'\0');
        strftime(sz.data(), sz.size(),fmt,&timeptr);
        sz.resize(strlen(sz.data()));
        return sz;
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

    inline std::vector<std::string>  strSplit(std::string str, const char delim , bool removeEmpty =false, bool strip = true) {
        std::vector<std::string> ret;
        std::istringstream ss(str);
        std::string v;
        while( getline(ss, v, delim)){
            v = strip?trim(v):v;
            if (removeEmpty && v == "" ) {
                continue;
            }
            ret.push_back(v);
        }
        return ret;
    }
};

