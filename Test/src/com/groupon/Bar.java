package com.groupon;

import java.util.Comparator;

public class Bar extends Boo {
	Bar(){
		
	}
	Bar(String s){
		super(s);
	}
	void zoo()
	{
		
	}
	
	final Comparator<String> test = new Comparator<String>() {

		@Override
		public int compare(String o1, String o2) {
			// TODO Auto-generated method stub
			return 0;
		}
	};
}
