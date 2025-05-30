
import prisma from "../../shared/prisma-client/prisma-client.js";


export const getAllGroceries = async () => {
  return await prisma.grocery.findMany();
};


export const getGroceryByItemCode = async (itemCode: string) => {
  return await prisma.grocery.findUnique({
    where: { itemCode },
  });
};

export const getGroceryHistory = async (itemCode: string) => {
  return await prisma.store_grocery_price_history.findMany({
    where: { itemCode },
    include: {
      stores: true, // ודא שזה השם הנכון של היחס ב-Prisma schema שלך
    },
    orderBy: [
      { StoreId: 'asc' },
      { updateDatetime: 'asc' },
    ],
  });
};
export const getStoresByItemCode = async (itemCode: string) => {
  return await prisma.store_grocery.findMany({
    where: { itemCode },
    include: {
      stores: true, // This pulls the full store data
    },
  });
};


// search groceries
export const searchGroceries = async (query: string) => {
  return await prisma.grocery.findMany({
    where: {
      OR: [
        // {
        //   manufacturerItemDescription: {
        //     startsWith: query,
        //     not: null,
        //   },
        // },
        {
          itemName: {
            startsWith: query,
            not: null,
          },
        },
      ],
    },
    take: 5,
  });
};

