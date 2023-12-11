all:spdlog/INSTALL twsapi_macunix.1019.02/IBJts/API_VersionNum.txt csv-parser/README.md json/README.md IntelRDFPMathLib20U2/LIBRARY/libbid.a

# https://github.com/gabime/spdlog
spdlog/INSTALL:
	git clone git@github.com:gabime/spdlog.git

# https://interactivebrokers.github.io/tws-api/initial_setup.html#install
# https://interactivebrokers.github.io/#
#
twsapi_macunix.1019.02/IBJts/API_VersionNum.txt:
	curl -O "https://interactivebrokers.github.io/downloads/twsapi_macunix.1019.02.zip"
	mkdir twsapi_macunix.1019.02
	unzip -d twsapi_macunix.1019.02  twsapi_macunix.1019.02.zip

# https://github.com/nlohmann/json
json/README.md:
	git clone git@github.com:nlohmann/json.git

# https://github.com/vincentlaucsb/csv-parser
csv-parser/README.md:
	git clone git@github.com:vincentlaucsb/csv-parser.git


IntelRDFPMathLib20U2/LIBRARY/libbid.a: IntelRDFPMathLib20U2.tar.gz
	tar xf $<
	make -C IntelRDFPMathLib20U2/LIBRARY CC=gcc  CALL_BY_REF=0 GLOBAL_RND=0 GLOBAL_FLAGS=0 UNCHANGED_BINARY_FLAGS=0

#- https://www.intel.com/content/www/us/en/developer/articles/tool/intel-decimal-floating-point-math-library.html
#- https://www.netlib.org/misc/intel/
IntelRDFPMathLib20U2.tar.gz:
	curl -o $@ "https://www.netlib.org/misc/intel/IntelRDFPMathLib20U2.tar.gz"

clean:
	rm  -fr twsapi_macunix.1019.02*
	rm -fr IntelRDFPMathLib20U2*

.PHONY: spdlog clean
