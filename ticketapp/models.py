from django.db import models

# Create your models here.

# Used to model tickets that are favorites. Can be saved and will be used for CRUD.
class SavedTicket(models.Model):
    name = models.CharField(max_length=100)
    ticket_url = models.URLField()
    image_url = models.URLField()
    date = models.CharField(max_length=100)
    time = models.CharField(max_length=50)
    venue = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    user_notes = models.TextField(blank=True)

    def __str__(self):
        return self.name