package com.barclay;

import java.util.ArrayList;
import java.util.List;

public class FibonnaciSeries {

	public static void main(String[] args) {
		List<Long> fibo = generateFibonnaci(5);
		for(Long i : fibo){
			System.out.print(i+", ");
		}
	}

	static List<Long> generateFibonnaci(int num){
		List<Long> fibo = new ArrayList<Long>();
		Long feb1=(long) 0;
		Long feb2=(long) 1;
		for (int i=0; i<num;i++){
			if(i == 0 || i == 1)
				fibo.add((long) 1);
			else{
				Long feb = feb1+feb2;
				feb2=feb1;
				feb1=feb;
				fibo.add(feb);
			}
		}
		return fibo;
	}
}
