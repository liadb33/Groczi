export const storePrompt = `
אתה מקבל אובייקט JSON המכיל מידע על חנות אך הערכים שלו מבולגנים בין השדות. 
סדר את הערכים של השדות הבאים בלבד: "storename", "address", "city", "zipcode".

הנחיות:
- ערך השדה "zipcode" יכול להיות רק מחרוזת של 7 ספרות בדיוק. אם הערך שנמצא אינו עומד בתנאי הזה, יש להגדיר אותו כ-null.
- ייתכן שחלק מהשדות חסרים, אם שדה חסר יש למלא אותו בערך null.
- אם השדה "subchainname" קיים, והוא אינו ריק ואינו מכיל ספרות, יש לשים את ערכו במקום "storename" בתוצאה.
- אם השדה "subchainname" הוא מספר (כלומר, מכיל רק ספרות), יש לשים במקום "storename" את הערך של "chainname".
- אם בשדה "storename" יש כתובת כלולה בתוך הטקסט (למשל, אחרי שם החנות מופיעה כתובת עם רחוב, מספר, עיר וכדומה, מופרדת בפסיק), יש לחלץ את הכתובת ולהעביר אותה לשדה "address". בשדה "storename" יש להשאיר רק את שם החנות בלי הכתובת.
- אם בשדה "address" יש עיר או מיקוד, יש להוציא אותם לשדות המתאימים ("city" או "zipcode") בהתאם למידע הזמין.
- אם בשדה "address" יש כתובת אתר (URL), יש להוסיף את המילה "אתר" בתחילת מחרוזת ה-"storename".

התוצאה צריכה להיות JSON בלבד, ללא טקסט נוסף.
`;

export const groceryPrompt = ``;
