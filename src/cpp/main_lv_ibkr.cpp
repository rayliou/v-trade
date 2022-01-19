//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"
#include "BigTable.h"
#include "./3rd-party/JohansenCointegration/JohansenHelper.h"

class Cointegrate{
public:
    Cointegrate(const char * bigCsvPath, int maxDays = 28);
    void run(const char * endDate);
private:
    // float coint(string & n1, string & n2, string & start, const string & end);
private:
    vector<string> m_symList;
    BigTable m_bigtable;

};
Cointegrate::Cointegrate(const char * bigCsvPath, int maxDays ):m_bigtable(bigCsvPath) {
    m_bigtable.read_csv(bigCsvPath);
    m_symList = m_bigtable.getSymbolList();

}
void Cointegrate::run(const char * endDate){
    int N = m_symList.size();
    int totalCnt = N*(N-1)/2;
    int cnt = 0;
    for (int i =0; i < N; i++){
        for (int j =i+1; j < N; j++){
            auto n1 = m_symList.at(i);
            auto n2 = m_symList.at(j);
            // auto start = 1;
            // auto end = 1;
            for (int k = 1; k <= 4; k++){
                auto idxPosRange = m_bigtable.getIndexRange(endDate,7*k);
                printf("[%d/%d][%s-%s] [%s:%ld][%s:%ld]\n", cnt,totalCnt ,n1.c_str(),n2.c_str(),
                 idxPosRange.first->first.c_str(), idxPosRange.first - m_bigtable.m_index.begin()
                 ,idxPosRange.second->first.c_str(), idxPosRange.second - m_bigtable.m_index.begin()
                 );
                int idxStart = idxPosRange.first - m_bigtable.m_index.begin();
                int idxEnd = idxPosRange.second - m_bigtable.m_index.begin();

                auto matchN1 = [&](const ColumnData::value_type &v){ return v.first  == n1 + "_close"; };
                auto matchN2 = [&](const ColumnData::value_type &v){ return v.first  == n2 + "_close"; };
                auto itN1 = std::find_if(m_bigtable.m_columnData.begin(),m_bigtable.m_columnData.end(),matchN1);
                auto itN2 = std::find_if(m_bigtable.m_columnData.begin(),m_bigtable.m_columnData.end(),matchN2);
                #if 0
                printf("\t[%s-%s][%f,%f]\n", 
                    itN1->first.c_str(),
                    itN2->first.c_str(),
                    itN1->second[0],
                    itN2->second[0]
                );
                #endif
                double *X = itN1->second.data() + idxStart;
                double *Y = itN2->second.data() + idxStart;
                int len = idxEnd - idxStart;

                DoubleMatrix xMat;
                int nlags = 1;
                xMat.resize(2);
                xMat[0].clear();
                xMat[1].clear();
                std::copy(X, X+len, std::back_inserter(xMat[0]));
                std::copy(Y, Y+len, std::back_inserter(xMat[1]));

                vector<MaxEigenData> outStats;
                DoubleVector eigenValuesVec;
                DoubleMatrix eigenVecMatrix;
                JohansenHelper johansenHelper(xMat);
                johansenHelper.DoMaxEigenValueTest(nlags);
                int cointCount = johansenHelper.CointegrationCount();
                outStats = johansenHelper.GetOutStats();
                printf("%d\n",cointCount);


            }

            // #float p = this->coint(n1,n2,start,end);
                // v = {'pair': f'{k1}_{k2}', 'p': p, 'pmin':pMin, 'start_of_pmin':start_of_pmin,}# 'plist': pList }
                // merge........


            cnt ++;

        }
    }

}





int main(int argc, char * argv[]) {
    if (argc <2){
        cout << "csv file path is needed" << endl;
        return 1;
    }
    auto filePath  = argv[1];
    const char * endDate = argv[2];
    // const char * endDate = "2022-01-13 08:09:0";
    Cointegrate c(filePath);
    c.run(endDate);
    return 0;
}
