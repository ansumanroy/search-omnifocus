from __future__ import unicode_literals

NAME_SORT = "name ASC"
TASK_SELECT = ("t.persistentIdentifier, t.name, t.dateCompleted, "
               "t.blockedByFutureStartDate, c.name, p.name, t.flagged, t.dateToStart, "
               "t.inInbox, t.effectiveInInbox, t.effectiveDateToStart, t.childrenCountAvailable, "
               "t.blocked, pi.status, t.effectiveFlagged, t.dateModified, t.containingProjectInfo, t.dateDue")
TASK_FROM = ("((task tt left join projectinfo pi on tt.containingprojectinfo=pi.pk) t left join "
             "task p on t.task=p.persistentIdentifier) left join "
             "context c on t.context = c.persistentIdentifier")
TASK_WHERE = "(t.containingProjectInfo <> t.persistentIdentifier OR t.containingProjectInfo is NULL) "
TASK_NAME_WHERE = "t.dateCompleted IS NULL AND lower(t.name) LIKE lower('%{0}%') AND "
NOT_COMPLETED_CLAUSE = "t.dateCompleted IS NULL"
ACTIVE_CLAUSE = "t.blocked = 0 AND "
CTX_SELECT = "persistentIdentifier, name, allowsNextAction, active, availableTaskCount"


def search_tasks(active_only, flagged, query, everything=None):
    where = (TASK_NAME_WHERE + TASK_WHERE).format(query)

    if active_only:
        where = "(t.blocked = 0 AND t.blockedByFutureStartDate = 0) AND " + where

    if flagged:
        where = "(t.flagged = 1 OR t.effectiveFlagged = 1) AND " + where

    if not everything:
        where = "(t.effectiveInInbox = 0 AND t.inInbox = 0) AND " + where

    return _generate_query(TASK_SELECT, TASK_FROM, where, "t." + NAME_SORT)


def search_inbox(query):
    where = "(t.effectiveInInbox = 1 OR t.inInbox = 1)"
    where = (TASK_NAME_WHERE + where).format(query)
    return _generate_query(TASK_SELECT, TASK_FROM, where, "t." + NAME_SORT)


def search_projects(active_only, query):
    select = ("p.pk, t.name, p.status, p.numberOfAvailableTasks, p.numberOfRemainingTasks, "
              "p.containsSingletonActions, f.name, t.dateToStart, t.effectiveDateToStart")
    from_ = ("(ProjectInfo p LEFT JOIN Task t ON p.task=t.persistentIdentifier) "
             "LEFT JOIN Folder f ON p.folder=f.persistentIdentifier")
    where = "lower(t.name) LIKE lower('%{0}%')".format(query)
    order_by = "p.containsSingletonActions DESC, t.name ASC"

    if active_only:
        where = "p.status = 'active' AND " + where

    return _generate_query(select, from_, where, order_by)


def search_contexts(query):
    select = "persistentIdentifier, name, allowsNextAction, active, availableTaskCount"
    where = "active = 1"
    if query:
        where = where + " AND lower(name) LIKE lower('%{0}%')".format(query)

    return _generate_query(select, "Context", where, NAME_SORT)


def search_folders(query):
    select = "persistentIdentifier, name, active, effectiveActive"
    where = "(active = 1 OR effectiveActive = 1)"
    if query:
        where = where + " AND lower(name) LIKE lower('%{0}%')".format(query)

    return _generate_query(select, "Folder", where, NAME_SORT)


def search_notes(active_only, flagged, query):
    select = TASK_SELECT + ", t.plainTextNote "
    where = "t.dateCompleted IS NULL AND lower(t.plainTextNote) LIKE lower('%{0}%')".format(query)

    if active_only:
        where = where + " AND (t.blocked = 0 AND t.blockedByFutureStartDate = 0)"

    if flagged:
        where = where + " AND (t.flagged = 1 OR t.effectiveFlagged = 1)"

    return _generate_query(select, TASK_FROM, where, "t." + NAME_SORT)


def show_recent_tasks(active_only):
    if active_only:
        return _generate_query(TASK_SELECT, TASK_FROM, NOT_COMPLETED_CLAUSE,
                               "t.dateModified DESC") + " LIMIT 10"
    else:
        return "SELECT {0} FROM {1} ORDER BY {2} LIMIT {3}".format(TASK_SELECT, TASK_FROM,
                                                                   "t.dateModified DESC", 10)


def show_due_tasks():
    return _generate_query(TASK_SELECT, TASK_FROM,
                           NOT_COMPLETED_CLAUSE + " AND (t.isDueSoon or t.isOverdue)",
                           "t.dateDue ASC") + " LIMIT 10"


def _generate_query(select, from_, where, order_by):
    return "SELECT {0} FROM {1} WHERE {2} ORDER BY {3}".format(select, from_, where, order_by)
