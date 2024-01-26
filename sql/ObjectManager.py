# create and maintain a connection pool here
# a connection pool holds constant connections to the db as opening and closing connections is expensive
# also allows for concurrent reads making it easier to serve larger numbers of requests
# -> concurrent connections introduce the need for locking
# -> (don't want to read a teacher from db at same time that user's entry gets updated)