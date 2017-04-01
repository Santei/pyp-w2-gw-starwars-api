# PYTHONPATH=. py.test ./tests/test_models.py::PeopleTestCase::test_people_model
import six

from starwars_api.client import SWAPIClient
from starwars_api.exceptions import SWAPIClientError

api_client = SWAPIClient()


class BaseModel(object):

    def __init__(self, json_data):
        """
        Dynamically assign all attributes in `json_data` as instance
        attributes of the Model.
        """
        for key, value in six.iteritems(json_data):
            setattr(self, key, value)


    @classmethod
    def get(cls, resource_id):
        """
        Returns an object of current Model requesting data to SWAPI using
        the api_client.
        """
        func = 'get_{}'.format(cls.RESOURCE_NAME)
        json_data = getattr(api_client, func)(resource_id)
         # remember that the result of the `get()` method must be an instance
         # of the model. That's why we need to instantiate `cls`, which
         # represents the current Model class (either People or Films)
        return cls(json_data)

    @classmethod
    def all(cls):
        """
        Returns an iterable QuerySet of current Model. The QuerySet will be
        later in charge of performing requests to SWAPI for each of the
        pages while looping.
        """
        qs = '{}QuerySet'.format(cls.RESOURCE_NAME.title())
        return eval(qs)()

class People(BaseModel):
    """Representing a single person"""
    RESOURCE_NAME = 'people'

    def __init__(self, json_data):
        super(People, self).__init__(json_data)

    def __repr__(self):
        return 'Person: {0}'.format(self.name)


class Films(BaseModel):
    RESOURCE_NAME = 'films'

    def __init__(self, json_data):
        super(Films, self).__init__(json_data)

    def __repr__(self):
        return 'Film: {0}'.format(self.title)


class BaseQuerySet(object):

    def __init__(self):
        self.current_page = 1
        self.current_element = 0

        # Variable to keep track of total count of our resources
        # We have no idea what the count is until we make the api request in the
        # _get_next_page function
        self.total_count = None
        # this attribute will contain the concatenation of all elements we get
        # in the successive requests to next pages. Meaning that, if we have
        # 10 results per page, after requesting the second page we will
        # see 20 elements in `self.objects`
        self.objects = []


    def __iter__(self):
        return self

    def __next__(self):
        """
        Must handle requests to next pages in SWAPI when objects in the current
        page were all consumed.
        """
        if self.current_element + 1 > len(self.objects):
            # get next page
            try:
                self._request_next_page()
            except SWAPIClientError:
                raise StopIteration
        elem = self.objects[self.current_element]
        self.current_element += 1
    
        return elem

    next = __next__

    def _request_next_page(self):
        """
        Request the next page of elements from the API based on the current state of the iteration
        """
        
        # make request in a generic way
        func = 'get_{}'.format(self.RESOURCE_NAME)
        method = getattr(api_client, func)
        json_data = method(**{'page': self.current_page})
        self.total_count = json_data["count"]
 
        # Get the correct model class based on RESOURCE_NAME
        Model = eval(self.RESOURCE_NAME.title())
        # enumerate new data
        for resource_data in json_data["results"]:
            self.objects.append(Model(resource_data))

        # increment our page counter
        self.current_page += 1
  
    def count(self):
        """
        Returns the total count of objects of current model.
        If the counter is not persisted as a QuerySet instance attr,
        a new request is performed to the API in order to get it.
        """
        if self.total_count is None:
            self._request_next_page()
        return self.total_count

class PeopleQuerySet(BaseQuerySet):
    RESOURCE_NAME = 'people'

    def __init__(self):
        super(PeopleQuerySet, self).__init__()

    def __repr__(self):
        return 'PeopleQuerySet: {0} objects'.format(str(len(self.objects)))


class FilmsQuerySet(BaseQuerySet):
    RESOURCE_NAME = 'films'

    def __init__(self):
        super(FilmsQuerySet, self).__init__()

    def __repr__(self):
        return 'FilmsQuerySet: {0} objects'.format(str(len(self.objects)))
