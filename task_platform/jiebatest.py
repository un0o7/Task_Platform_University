import numpy as np
import jieba
"""创建数据集"""


def loadDataSet():
    postingList = [['我', '江安', '菜鸟', '帮忙', '代取', '华西', '打印'],
                   ['代写', '代课', '早上', '代抄 ','代签到', '求', '点名', 'stupid'],  # stupid侮辱类
                   ['my', '螺狮粉', '请问', '求', '取', '舍', '晚上', '自习'],
                   ['互助', '选', '收', '求', '代'],  # garbage,stupid侮辱类
                   ['丢失', 'npy', '出', '组队', '望江', '代价', '拼单', '江安', '收'],
                   ['代课', '课程', '论文', '收', '代写', '代签到','点名']]  # stupid侮辱类
    classVec = [0, 1, 0, 1, 0, 1]  # 类别标签向量，1代表侮辱性词汇，0代表不是
    return postingList, classVec


"""创建词汇表"""


def createVocabList(dataSet):
    vocabSet = set([])
    for document in dataSet:  # 取出每一行文档（每行七个单词）
        vocabSet = vocabSet | set(document)  # 先将文档转换为set集合，无需不重复，再取并集
    return list(vocabSet)


"""判断输入集中单词是否在词汇表中"""


def setOfWordsVec(vocabList, inputSet):

    returnVec = [0] * len(vocabList)  # 创建一个元素都为0的向量
    for word in inputSet:  # 取输入集的每一个单词
        if word in vocabList:  # 如果单词在词汇表中
           returnVec[vocabList.index(word)] = 1  # 标志位置为一，表示所检测单词在词汇表中
        #for i in vocabList:
        #    if i.find(word):
        #        print(word)
        #        returnVec[vocabList.index(i)] = 1
        #        break
        #else:
           # print("the word:%s is not in my Vocabulary!" % word)

    return returnVec


"""计算概率"""


def trainNB0(trainMatrix, trainCategory):
    numTrainDocs = len(trainMatrix)  # 样本个数，6
    numWords = len(trainMatrix[0])  # 每个样本长度，32
    pAbusive = sum(trainCategory) / float(numTrainDocs)  # 文档属于侮辱类的概率
    p0Num = np.ones(numWords)  # 非侮辱类情况下，某个单词出现的概率
    p1Num = np.ones(numWords)  # 侮辱类情况下，某个单词出现的概率
    p0Denom = 2.0  # 分母，都设置为2（我们需要的是两个比较，所以都设置为共同的分母不影响大小）
    p1Denom = 2.0
    for i in range(numTrainDocs):
        if trainCategory[i] == 1:
            p1Num += trainMatrix[i]  # 每个侮辱类样本都相加（记录侮辱类每个单词的个数）
            p1Denom += sum(trainMatrix[i])  # 求和所有侮辱类样本的单词数
        else:
            p0Num += trainMatrix[i]  # 每个非侮辱类样本都相加（记录侮辱类每个单词的个数）
            p0Denom += sum(trainMatrix[i])  # 求和所有非侮辱类样本的单词数
    p1Vect = np.log(p1Num / p1Denom)  # 取对数，防止下溢出
    p0Vect = np.log(p0Num / p0Denom)
    return p0Vect, p1Vect, pAbusive


"""分类"""


def classifyNB(vecClassify, p0Vec, p1Vec, pClass1):
    p1 = sum(vecClassify * p1Vec) + np.log(pClass1)  # log(A*B)=logA+logB，前边没有log，是因为这需要两个数比较，同时log和都不log不会影响比较大小
    p0 = sum(vecClassify * p0Vec) + np.log(1 - pClass1)
    if p1 > p0:
        return 1
    else:
        return 0

def classifier(s):
    testEntry=jieba.lcut(s)
    listOposts, listClasses = loadDataSet()
    myVocabList = createVocabList(listOposts)
    trainMat = []
    for postinDoc in listOposts:
        trainMat.append(setOfWordsVec(myVocabList, postinDoc))  # 生成6*32的矩阵，表示每条数据中单词在词汇表的存在情况
    poV, p1V, pAb = trainNB0(np.array(trainMat), np.array(listClasses))

    thisDoc = np.array(setOfWordsVec(myVocabList, testEntry))
    return  classifyNB(thisDoc, poV, p1V, pAb)


if __name__ == '__main__':
    print(classifier('近代史代抄代课'))
