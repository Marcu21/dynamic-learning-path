-- Create the platforms table first (if it doesn't exist)
CREATE TABLE IF NOT EXISTS platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    website_url VARCHAR(500)
);

-- Insert initial data
INSERT INTO platforms (name, website_url) VALUES
  ('Codeforces', 'https://codeforces.com/'),
  ('YouTube', 'https://www.youtube.com'),
  ('Spotify', 'https://open.spotify.com'),
  ('Google Books', 'https://books.google.com'),
  ('Research Papers', ''),
  ('Manual Search', '')
ON CONFLICT (name) DO NOTHING;

-- Verify the insert worked
SELECT COUNT(*) as total_platforms FROM platforms;