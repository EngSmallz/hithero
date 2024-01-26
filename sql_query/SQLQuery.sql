BULK INSERT StateCounty
FROM 'C:\Users\jstnb\OneDrive\Desktop\Scripts\hithero\static\other\uscounties.csv'
WITH (
    FIRSTROW = 2,  -- Skip header row
    FIELDTERMINATOR = ',',  -- CSV field delimiter
    ROWTERMINATOR = '\n',  -- Newline terminator
    CODEPAGE = 'ACP'  -- Windows-1252 encoding, adjust if needed
);
