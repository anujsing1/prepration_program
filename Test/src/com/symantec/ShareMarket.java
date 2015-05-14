package com.symantec;

public class ShareMarket {

	public static void main(String[] args) {
		int[] stockPrice = {10, 2, 15, 17, 6, 3, 1};
		int[] stocks = {10, 17, 2, 6, 15, 3, 1};
		share(stockPrice);
//		find(stocks);
//		findBuy$SellPeriod(0, 0, stockPrice);
	}

	
	static void share(int[] arr){
		int lIndex=0, rIndex=0, diff=0, maxD=0;
		
		for(int i=0; i< arr.length; i++){
			for(int j=i+1; j<arr.length; j++){
				diff = arr[j] - arr[i];
				if(maxD<diff){
					maxD = diff;
					lIndex = i;
					rIndex = j;
				}
			}
		}
		
		System.out.println("maxDiff : "+maxD+" - BuyIndex : "+lIndex+" - SellIndex : "+rIndex);
	}
	
	static void find(int[] stocks){
		int min=Integer.MAX_VALUE;
		int max=Integer.MIN_VALUE;
		int minIndex = 0,maxIndex =0;
		int maxDiff =0;
		int buy=0, sell=0;
		for (int i = 0; i < stocks.length; i++) {
			if (stocks[i] < min){
				min = stocks[i];
				minIndex = i;
			}
			if (stocks[i] > max){
				max = stocks[i];
				maxIndex = i;
			}
			int diff = max-min;
			if(diff >= maxDiff && minIndex <= maxIndex){
				buy = minIndex;
				sell = maxIndex;
				maxDiff = diff;
			}
		}
		System.out.println("maxDiff : "+maxDiff+" - BuyIndex : "+buy+" - SellIndex : "+sell);
	}
	
	static void findBuy$SellPeriod(int buy, int sell, int[] stockPrice){
		buy=Integer.MAX_VALUE;
		sell=Integer.MIN_VALUE;
		int profit=0;
		int buyDay = 0;
		int sellDay = 0;
		for(int i=0;i<stockPrice.length;i++){
			if(buy > stockPrice[i] && sellDay >= buyDay && i <= sellDay){
				buy = stockPrice[i];
				buyDay = i;
			}
			if(sell < stockPrice[i]){
				sell = stockPrice[i];
				sellDay = i;
			}
		}
		System.out.println("Buy : "+buy+" - Sell : "+sell);
	}
	
}
