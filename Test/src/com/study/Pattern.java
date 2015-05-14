package com.study;

public class Pattern extends AbstractClass implements ChildInterface {

	public static void main(String[] args) {
		// TODO Auto-generated method stub

		int temp = 0;
		for (int i=1; i<=5; i++)
		{
			for (int j=1; j<=i; j++)
			{
				temp = temp+i+j;
				System.out.println();
			}
		}
		
	}

	@Override
	public void c() {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void d() {
		// TODO Auto-generated method stub
		
	}

}
