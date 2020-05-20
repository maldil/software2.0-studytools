
from pyspark.ml.fpm import FPGrowth
from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql.functions import size
import argparse

sc = SparkContext('local')
spark = SparkSession(sc)
sc.setLogLevel("ERROR")
# FILE_PATH = '/Users/dilhara/Documents/TOSEM/DATA/multi_lib_upgrades.txt'
FILE_PATH = '/Users/dilhara/Documents/TOSEM/DATA/non_ml_lib_libs.txt'


def process():

   data_content = [x.strip().split(',') for x in open(FILE_PATH).readlines()]
   data_content_tuple = []
   for i in range(0,len(data_content)):
      data_content_tuple.append((i,data_content[i]))

   df = spark.createDataFrame(data_content_tuple, ["id", "items"])

   fpGrowth = FPGrowth(itemsCol="items", minSupport=0.1, minConfidence=0.5)
   model = fpGrowth.fit(df)

   # Display frequent itemsets.
   # model.freqItemsets

   model.freqItemsets.filter(size('items') > 0).orderBy('freq',ascending=0).show(50,False)

   print(type(model.freqItemsets))


   # Display generated association rules.
   model.associationRules.orderBy('confidence',ascending=0).show(200,False)

   # transform examines the input items against all the association rules and summarize the
   # consequents as prediction
   model.transform(df).show(50,False)



if __name__== "__main__":
    parser = argparse.ArgumentParser(description='Process Software 2.0.')
    parser.add_argument('CSV_FILE', type=str,
                        help='project download path')
    args = parser.parse_args()
    process(args.CSV_FILE)
