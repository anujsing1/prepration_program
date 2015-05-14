package com.java2novoice;

public class PrimeNo {

	public static void main(String[] args) {
		System.out.println(isPrime(17));
	}
	
	static boolean isPrime(int num){
		for(int i=2;i<num;i++){
			if(num%i == 0)
				return false;
		}
		return true;
	}

}
