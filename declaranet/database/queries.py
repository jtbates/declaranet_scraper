def one_or_create(row, session):
    filters = []
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if value is not None:
            filter = (column == value)
            filters.append(filter)
    q = session.query(type(row)).filter(*filters)
    res = q.one_or_none()
    if res is None:
        session.add(row)
        session.commit()
        return(row)
    else:
        return(res)


def one_like(row, session, like_cols=['NAME'],
             replace_like_chars={'?': '_'}):
    filters = []
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if value is not None:
            if column.name in like_cols:
                for x, y in replace_like_chars.items():
                    value = value.replace(x, y)
                filter = column.like(value)
            else:
                filter = (column == value)
            filters.append(filter)
    q = session.query(type(row)).filter(*filters)
    return(q.one_or_none())

