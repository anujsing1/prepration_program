package com.barclay;

public class Factorial {

	public static void main(String[] args) {
		System.out.println(findFactorial(3));
	}

	static long findFactorial(int num){
		long fact=1;
		if(num == 0)
			return fact;
		for(int i=num;i>0;i--){
			fact = fact*i;
		}
		return fact;
	}
}
