"""
Mars Weather Summary
Reads mars_weathers_data.csv and inserts the data into MySQL.
Query results are saved as a PNG chart.
"""

import csv
import struct
import zlib

import mysql.connector


CSV_FILE = 'mars_weathers_data.csv'
PNG_FILE = 'mars_weather_summary.png'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'mars_db',
}

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS mars_weather (
        weather_id INT AUTO_INCREMENT PRIMARY KEY,
        mars_date  DATETIME NOT NULL,
        temp       INT,
        storm      INT
    )
"""


class MySQLHelper:
    """Provides database connection and query execution helpers."""

    def __init__(self, host, user, password, database):
        self._host = host
        self._user = user
        self._password = password
        self._database = database
        self._connection = None
        self._cursor = None

    def connect(self):
        self._connection = mysql.connector.connect(
            host=self._host,
            user=self._user,
            password=self._password,
            database=self._database,
        )
        self._cursor = self._connection.cursor()

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()

    def execute(self, query, params=None):
        self._cursor.execute(query, params or ())
        self._connection.commit()

    def fetch_all(self, query, params=None):
        self._cursor.execute(query, params or ())
        return self._cursor.fetchall()


class PngWriter:
    """Minimal PNG image writer using only the Python standard library."""

    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._pixels = [[(255, 255, 255)] * width for _ in range(height)]

    def set_pixel(self, x, y, color):
        if 0 <= x < self._width and 0 <= y < self._height:
            self._pixels[y][x] = color

    def fill_rect(self, x, y, w, h, color):
        for j in range(y, min(y + h, self._height)):
            for i in range(x, min(x + w, self._width)):
                self.set_pixel(i, j, color)

    def draw_line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def save(self, file_path):
        def make_chunk(chunk_type, data):
            body = chunk_type + data
            crc = zlib.crc32(body) & 0xFFFFFFFF
            return struct.pack('>I', len(data)) + body + struct.pack('>I', crc)

        # IHDR: width, height, bit_depth=8, color_type=2(RGB),
        #        compression=0, filter=0, interlace=0
        ihdr = struct.pack(
            '>IIBBBBB',
            self._width, self._height,
            8, 2, 0, 0, 0,
        )

        raw = bytearray()
        for row in self._pixels:
            raw.append(0)  # filter type: None
            for r, g, b in row:
                raw.extend((r, g, b))

        compressed = zlib.compress(bytes(raw), 9)

        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(make_chunk(b'IHDR', ihdr))
            f.write(make_chunk(b'IDAT', compressed))
            f.write(make_chunk(b'IEND', b''))


def read_csv(file_path):
    rows = []
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'mars_date': row['mars_date'],
                'temp': int(row['temp']),
                'storm': int(row['storm']),
            })
    return rows


def insert_weather_data(helper, rows):
    insert_sql = (
        'INSERT INTO mars_weather (mars_date, temp, storm) '
        'VALUES (%s, %s, %s)'
    )
    for row in rows:
        helper.execute(insert_sql, (row['mars_date'], row['temp'], row['storm']))


def save_chart_png(rows, file_path):
    width = 800
    height = 400
    margin = 40
    chart_w = width - 2 * margin
    chart_h = height - 2 * margin

    png = PngWriter(width, height)

    # Background and chart area
    png.fill_rect(0, 0, width, height, (235, 240, 248))
    png.fill_rect(margin, margin, chart_w, chart_h, (255, 255, 255))

    n = len(rows)
    if n == 0:
        png.save(file_path)
        return

    temps = [row['temp'] for row in rows]
    min_temp = min(temps) - 5
    max_temp = max(temps) + 5
    temp_range = max_temp - min_temp

    def to_x(i):
        return margin + int(i / max(n - 1, 1) * chart_w)

    def to_y(temp):
        return margin + chart_h - int((temp - min_temp) / temp_range * chart_h)

    # Horizontal grid lines (4 lines)
    for k in range(1, 5):
        gy = margin + int(k / 5 * chart_h)
        for x in range(margin, margin + chart_w):
            png.set_pixel(x, gy, (210, 215, 225))

    # Storm markers (light red vertical bars)
    for i, row in enumerate(rows):
        if row['storm']:
            x = to_x(i)
            png.fill_rect(x - 3, margin, 6, chart_h, (255, 210, 210))

    # Axes
    for x in range(margin, margin + chart_w + 1):
        png.set_pixel(x, margin + chart_h, (60, 60, 60))
    for y in range(margin, margin + chart_h + 1):
        png.set_pixel(margin, y, (60, 60, 60))

    # Temperature line
    for i in range(n - 1):
        x0, y0 = to_x(i), to_y(temps[i])
        x1, y1 = to_x(i + 1), to_y(temps[i + 1])
        for thickness in range(-1, 2):
            png.draw_line(x0, y0 + thickness, x1, y1 + thickness, (30, 100, 200))

    # Data points
    for i, row in enumerate(rows):
        x, y = to_x(i), to_y(row['temp'])
        color = (200, 40, 40) if row['storm'] else (30, 100, 200)
        png.fill_rect(x - 4, y - 4, 8, 8, color)

    png.save(file_path)
    print(f'Chart saved to {file_path}')


def main():
    # 1. Read CSV
    rows = read_csv(CSV_FILE)
    print(f'Read {len(rows)} rows from {CSV_FILE}')
    for row in rows:
        print(row)

    # 2. Connect to MySQL
    helper = MySQLHelper(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
    )
    helper.connect()

    # 3. Create table
    helper.execute(CREATE_TABLE_SQL)
    print('\nTable mars_weather is ready.')

    # 4. Insert data
    insert_weather_data(helper, rows)
    print(f'Inserted {len(rows)} rows into mars_weather.')

    # 5. Fetch and display results
    results = helper.fetch_all(
        'SELECT weather_id, mars_date, temp, storm '
        'FROM mars_weather ORDER BY weather_id'
    )
    print('\nDatabase contents:')
    for record in results:
        print(record)

    helper.close()

    # 6. Save result as PNG chart
    save_chart_png(rows, PNG_FILE)


if __name__ == '__main__':
    main()
