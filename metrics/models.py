from django.db import models

class TrelloBoard(models.Model):
    team = models.ForeignKey('Team')
    hash_id = models.CharField(max_length=30)
    ignore_list = models.CharField(max_length=255)
    
    def __str__(self):
        return '%s - %s' % (self.team, self.hash_id)
    
class KanbanStatus(models.Model):
    name = models.CharField(max_length=255)
    groups_status = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    
class KanbanStatusSynonym(models.Model):
    kanban_status = models.ForeignKey('KanbanStatus')
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return '%s - %s' % (self.kanban_status, self.name)
    
class Team(models.Model):
    team_name = models.CharField(max_length=30)
    
    def __str__(self):
        return self.team_name
    
class Release(models.Model):
    teams = models.ManyToManyField('Team')
    name = models.CharField(max_length=250)
    start = models.DateField()
    end = models.DateField()
    
    def __str__(self):
        return self.name

class TeamMember(models.Model):
    team = models.ForeignKey('Team')
    name =  models.CharField(max_length=100)
    image = models.ImageField(upload_to='metrics/metrics/htdocs/static/uploads/')

    def __str__(self):
        return self.name
