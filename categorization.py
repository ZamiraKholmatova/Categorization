import psycopg2
from sklearn.feature_extraction.text import CountVectorizer
from methodology import *

# files = files_dict('С:\\Users\\z.kholmatova\\Downloads\\Categorization')
files = files_dict("Categorization")

new_files = dict()
list_of_categories = []
for filename in files:
    new_files[filename] = set(files[filename])
    list_of_categories.append(filename)

# remove unnecessary intersections

for category_name in list_of_categories:
    if category_name != 'Utilities':
        new_files['Utilities'] = new_files['Utilities'] - new_files[category_name]
new_files['Development'] = new_files['Development'] - new_files['Development'].intersection(new_files['Management'])
new_files['Management'] = new_files['Management'] - new_files['Development'].intersection(new_files['Management'])
new_files['Education'] = new_files['Education'] - new_files['Education'].intersection(new_files['Management'])
new_files['Management'] = new_files['Management'] - new_files['Education'].intersection(new_files['Management'])
for category_name in list_of_categories:
    if category_name != 'Entertainment':
        new_files['Entertainment'] = new_files['Entertainment'] - new_files[category_name]
for category_name in list_of_categories:
    if category_name != 'Communication':
        new_files[category_name] = new_files[category_name] - new_files['Communication']
new_files['Education'] = new_files['Education'].intersection(new_files['Development'])

# removing ends here


all_data = []
for filename in new_files:
    all_data.extend(new_files[filename])
data_ranges = []
t = 0
for filename in new_files:
    data_ranges.append((filename, len(new_files[filename]) + t))
    t += len(new_files[filename])
vectorizer = CountVectorizer(stop_words='english')
counts_data = vectorizer.fit_transform(all_data)
terms = vectorizer.get_feature_names()
inf = codecs.open('uncategorized.txt', "r", "utf_8_sig")
uncategorized = [x.lower().strip().strip('\r') for x in inf.read().split('\n')]
#print(uncategorized)



try:
    connection = psycopg2.connect(user="postgres",
                                  password="1nn0M3tr1c5",
                                  host="10.90.138.244",
                                  port="5432",
                                  database="postgres")
    cursor = connection.cursor()
    '''
    category_to_id = ['Utilities', 'Entertainment', 'Development', 'Communication', 'Management',
                      'Education', 'Design_Creativity']
    for cat in category_to_id:
        insert_to_cl = " insert into innometricsconfig.cl_categories (catname, catdescription) " \
                       "values (%s,%s)"
        record_to_cl = (cat, 'new_desc')
        cursor.execute(insert_to_cl, record_to_cl)
        connection.commit()
        count = cursor.rowcount
        print(count, "Record inserted successfully into table")
    '''
    #postgreSQL_select_Query = "select * from innometrics.activity order by activityid"
    postgreSQL_select_Query = "select * from innometrics.activity order by activityid"

    cursor.execute(postgreSQL_select_Query)
    activity_records = cursor.fetchall()

    for row in activity_records:
        #print(row)
        name = ''
        category = ''
        executable = row[6]
        #print(executable)
        q = get_app_name(row[6])
        psql = "select exists (select from innometricsconfig.cl_apps_categories where executablefile=%s)"
        cursor.execute(psql, (executable,))
        res = cursor.fetchone()[0]
        #print(res)
        if q not in uncategorized:
            if not res:
                if q in all_data:
                    #print('\033[1m' + get_doc_category(all_data.index(q), data_ranges) + '\033[0m', q)
                    category = get_doc_category(all_data.index(q), data_ranges)
                    name = q
                else:
                    if row[8] is not None:
                        if len(row[8]) != 0:
                            q = row[8]
                    processes_to_categories = process_query(q, counts_data, terms, data_ranges, all_data)
                    for element in processes_to_categories:
                        #print('\033[1m' + element[0] + '\033[0m', element[1])
                        category = element[0]
                        name = element[1]

                select_cat_id = "select * from innometricsconfig.cl_categories where catname=%s"
                cursor.execute(select_cat_id, (category,))
                category_id = cursor.fetchone()[0]

                insert_to_appcl = " insert into innometricsconfig.cl_apps_categories (catid, appname, appdescription" \
                                  ", executablefile) values (%s,%s,%s,%s)"
                record_to_appcl = (category_id, name, 'asd', executable)
                cursor.execute(insert_to_appcl, record_to_appcl)
                connection.commit()
                #print('Add to app_cl')

            else:
                category, name = if_exists(executable, cursor)
                #print('\033[1m' + category + '\033[0m', name)

        #else:
        #   print('\033[1m' + 'Uncategorized' + '\033[0m', name)
        #   print("\n")

        # print("executable_name = ", row[6], )
        # print("browser_title  = ", row[8], len(row[8]), "\n")

except (Exception, psycopg2.Error) as error:
    print("Error while fetching data from PostgreSQL", error)

finally:
    # closing database connection.
    if (connection):
        cursor.close()
        connection.close()
        #print("PostgreSQL connection is closed")