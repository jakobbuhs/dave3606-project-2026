import psycopg

conn = psycopg.connect(
    host="localhost",
    port=9876,
    dbname="lego-db",
    user="lego",
    password="bricks",
)

cur = conn.cursor()
cur.execute(
    """
    create table lego_set(
        id text not null,
        name text not null,
        year int null,
        category text null,
        preview_image_url text null
    );
    """
)
cur.execute(
    """
    create table lego_brick(
        brick_type_id text not null,
        color_id int not null,
        name text not null,
        preview_image_url text null
    );
    """
)
cur.execute(
    """
    create table lego_inventory(
        set_id text not null,
        brick_type_id text not null,
        color_id int not null,
        count int not null
    );
    """
)
cur.execute(
    """
    ALTER TABLE lego_set ADD PRIMARY KEY (id);
    """
)
cur.execute(
    """
    ALTER TABLE lego_brick ADD PRIMARY KEY (brick_type_id, color_id);
    """
)
cur.execute(
    """
    ALTER TABLE lego_inventory ADD PRIMARY KEY (set_id, brick_type_id, color_id);
    """
)
cur.execute(
    """
    ALTER TABLE lego_inventory ADD FOREIGN KEY (set_id) REFERENCES lego_set(id);
    """
)
cur.execute(
    """
    ALTER TABLE lego_inventory ADD FOREIGN KEY (brick_type_id, color_id)
        REFERENCES lego_brick(brick_type_id, color_id);
    """
)
cur.close()
conn.commit()
conn.close()
