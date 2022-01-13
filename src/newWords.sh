#!/bin/bash
LANG=$1
U=$2
function usage
{
    echo Run cmd like:
    echo "cat someFile | $0 fr|en  henry|frank|lucy detail|no-detail"
    exit 1
}
if [ -z $3 ]; then
    usage
elif [ $3 != 'detail' -a $3 != 'no-detail' ]; then
    usage
fi

DETAIL=$3
if [ $U = 'henry' ]; then
    LANG=en
    TOPNN=6000
    TOPN=8000
elif [ $U = 'frank' ]; then
    LANG=fr
    TOPNN=1186
    TOPN=1186
else
    usage
fi;



CORE_NLP_DIR="$HOME/dict_tools/CoreNLP/stanford-corenlp-full-2018-10-05"
#echo $CORE_NLP_DIR
NLP_CMD_PREFIX="java -mx3g -cp '$CORE_NLP_DIR/*' "

function pipeCmd
{
    out_format="-outputFormat conll  -output.columns word,lemma,characteroffsetbegin,characteroffsetend"
    out_format="-outputFormat conll"
    #out_format="-outputFormat conllu  "
    if [ -z $1 ] ; then
        lang_property=$1
        echo 'Language must be either fr or en'; exit 1;
    elif [ $1 = 'fr' ] ; then
        lang_property=" -props StanfordCoreNLP-french.properties "
    elif [ $1 = 'en' ] ; then
        lang_property=''
    else
        echo 'Language must be either fr or en'; exit 1;
    fi
    echo "$NLP_CMD_PREFIX edu.stanford.nlp.pipeline.StanfordCoreNLP $lang_property -annotators 'tokenize,cleanxml, ssplit, pos, lemma, ner'   $out_format "

}
function webCmd
{
    lang_property=$1
    port=$2

}
NLP_CMD_PIPE=`pipeCmd $LANG`
#echo run $NLP_CMD_PIPE \| "$ICLOUD/en_vocabulary/tools/voc_tool/voc_tool.py" reading_to_words   -l $LANG   -u $U -N $TOPNN -n $TOPN --$DETAIL
#eval $NLP_CMD_PIPE 
eval $NLP_CMD_PIPE | "$ICLOUD/en_vocabulary/tools/voc_tool/voc_tool.py" reading_to_words   -l $LANG   -u $U -N $TOPNN -n $TOPN --$DETAIL
