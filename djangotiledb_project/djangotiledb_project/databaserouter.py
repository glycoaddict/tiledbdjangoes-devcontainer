class AnnoRouter:
    """
    A router to control all database operations on models in the
    annoquery applications.
    """
    annodb_name = 'annodb'

    route_app_labels = {'annoquery',}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return self.annodb_name
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write 
        """
        
        if model._meta.app_label in self.route_app_labels:                        
            return self.annodb_name
        return None

    # def allow_relation(self, obj1, obj2, **hints):
    #     """
    #     Allow relations if a model in the annoquery apps is
    #     involved.
    #     """
    #     if (
    #         obj1._meta.app_label in self.route_app_labels or
    #         obj2._meta.app_label in self.route_app_labels
    #     ):
    #        return True
    #     return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the annoquery apps only appear in the
        'annodb' database.
        """
        if app_label in self.route_app_labels:            
            return db == self.annodb_name
        else:
            return None
