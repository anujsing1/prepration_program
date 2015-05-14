package com.barclay;

import java.util.ArrayList;
import java.util.List;

public class PrimeNumber {

	public static void main(String[] args) {
		List<Integer> primeList = generateFirstNPrimeNumbers(50);
		for(long prime : primeList){
			System.out.print(prime+", ");
		}
	}

	static List<Integer> generateFirstNPrimeNumbers(int num){
		int i=1;
		int j=1;
		List<Integer> primeList = new ArrayList<Integer>();
		while(j<=num){
			if(isPrimeNum(i)){
				primeList.add(i);
				j++;
			}
			i++;
		}
		return primeList;
	}
	
	static boolean isPrimeNum(int num){
		boolean prime = true;
		for(int i=2;i<=num;i++){
			if(num != i && num%i==0){
				prime = false;
				break;
			}
		}
		return prime;
	}
}
