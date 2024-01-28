#CXX=/usr/local/Cellar/gcc/11.2.0_3/bin/g++-11 
#AR=/usr/local/Cellar/gcc/11.2.0_3/bin/gcc-ar-11

SRCS=$(shell ls *.cpp)
OBJS=$(patsubst %, %.o, $(basename $(SRCS)))
CXXFLAGS=-std=c++20 -g -O3
#-fPIC #-I/usr/local/Cellar/gcc/11.2.0_3/include/c++/11
#$(CXX) -shared  -Wl,-soname,$@ -o $@.1 $^

TARGET=libtws_ib.a

$(TARGET):$(OBJS)
	$(AR) rcs $@ $^
%.o:%.cpp
	$(CXX) $(CXXFLAGS) -c -MT $@ -MMD -MP -MF $*.d -o $@ $<

clean:
	rm -f *.o *.d *.a

-include $(patsubst %, %.d, $(basename $(SRCS)))
