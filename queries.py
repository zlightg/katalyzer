HOST = "postgresql://localhost/katalys"

from sqlalchemy import create_engine
from sqlalchemy import text
#from templateParser import messageStateProcessor, processTemplate
#from processor import Processor
from sqlalchemy import text


#p = Processor()

engine = create_engine(HOST, echo=True, future=True)
import contextlib

def connectivity(engine):
    connection = None

    @contextlib.contextmanager
    def connect():
        nonlocal connection

        if connection is None:
            connection = engine.connect()
            with connection:
                with connection.begin():
                    yield connection
        else:
            yield connection

    return connect
conn = connectivity(engine)

class Query:
  def execute(self, query):
    with engine.connect() as connection:
      result = connection.execute(text(query))
      return result.all()
  def insert(self, query):
    with engine.connect() as connection:
      connection.execute(text(query))
      connection.commit()

q = Query()
result = q.execute("Select * from activity")
result = q.execute("Select * from activity")




### TODO MOVE TO MODELS FILE BELOW
#processTemplate("$add($a,$add($b,$subtract($a,$b))) men $subtract($a,$b) went to $a and then to $b", {}, p)
#messageStateProcessor("$getLastMessageStateID($conversation_id)",{"user_id":1},p)
### TODO MOVE TO MODELS FILE ABOVE


